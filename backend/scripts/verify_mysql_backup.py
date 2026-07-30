#!/usr/bin/env python3
"""Restore a BuyHouse MySQL backup into an isolated temporary database.

The temporary database is dropped automatically unless --keep-test-database is
explicitly provided. The running business database is never altered.
"""
from __future__ import annotations

import argparse
import os
import re
import subprocess
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import unquote, urlsplit

BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from app.core.config import settings

DATABASE_PATTERN = re.compile(r"^[A-Za-z0-9_]+$")


def option_value(value: str) -> str:
    if "\n" in value or "\r" in value:
        raise ValueError("database connection value contains a newline")
    return '"' + value.replace("\\", "\\\\").replace('"', '\\"') + '"'


def create_option_file() -> Path:
    parsed = urlsplit(settings.DATABASE_URL)
    if not parsed.scheme.startswith("mysql"):
        raise ValueError("DATABASE_URL is not MySQL")
    if not parsed.username or parsed.password is None:
        raise ValueError("DATABASE_URL is missing database credentials")
    with tempfile.NamedTemporaryFile(
        mode="w", encoding="utf-8", prefix="buyhouse-restore-", suffix=".cnf", delete=False
    ) as handle:
        path = Path(handle.name)
        os.chmod(path, 0o600)
        handle.write(
            "[client]\n"
            f"host={option_value(parsed.hostname or 'localhost')}\n"
            f"port={parsed.port or 3306}\n"
            f"user={option_value(unquote(parsed.username))}\n"
            f"password={option_value(unquote(parsed.password))}\n"
        )
    return path


def mysql_command(option_path: Path, arguments: list[str], stdin=None) -> subprocess.CompletedProcess:
    command = ["mysql", f"--defaults-extra-file={option_path}", *arguments]
    return subprocess.run(command, stdin=stdin, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False)


def mysql_failure_detail(result: subprocess.CompletedProcess) -> str:
    error = result.stderr.decode("utf-8", errors="replace")
    match = re.search(r"ERROR\s*:?[\s]+(\d+)", error, flags=re.IGNORECASE)
    if match:
        return "mysql_error_" + match.group(1)
    if re.search(r"access denied", error, flags=re.IGNORECASE):
        return "mysql_access_denied"
    if re.search(r"unknown database", error, flags=re.IGNORECASE):
        return "mysql_unknown_database"
    if re.search(r"already exists", error, flags=re.IGNORECASE):
        return "mysql_object_already_exists"
    if re.search(r"SQL syntax", error, flags=re.IGNORECASE):
        return "mysql_sql_syntax_error"
    if re.search(r"unknown command", error, flags=re.IGNORECASE):
        return "mysql_unknown_command"
    if result.returncode < 0:
        return "mysql_process_terminated"
    return f"mysql_command_failed_rc_{result.returncode}"


def execute_or_raise(option_path: Path, arguments: list[str], stdin=None) -> subprocess.CompletedProcess:
    result = mysql_command(option_path, arguments, stdin=stdin)
    if result.returncode != 0:
        raise RuntimeError(mysql_failure_detail(result))
    return result


def restore_backup_or_raise(option_path: Path, database: str, backup: Path) -> None:
    decompressor = subprocess.Popen(
        ["gzip", "--decompress", "--stdout", "--", str(backup)],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    if decompressor.stdout is None or decompressor.stderr is None:
        raise RuntimeError("gzip_process_setup_failed")
    try:
        result = mysql_command(option_path, [database], stdin=decompressor.stdout)
    finally:
        decompressor.stdout.close()
    decompressor.stderr.read()
    decompressor.wait()
    if result.returncode != 0:
        raise RuntimeError(mysql_failure_detail(result))
    if decompressor.returncode != 0:
        raise RuntimeError("gzip_decompression_failed")


def main() -> int:
    parser = argparse.ArgumentParser(description="Verify a compressed BuyHouse SQL backup by isolated restore")
    parser.add_argument("--backup", required=True, type=Path)
    parser.add_argument("--keep-test-database", action="store_true")
    args = parser.parse_args()
    backup = args.backup.resolve()
    if not backup.is_file() or backup.suffix != ".gz":
        raise SystemExit("backup must be an existing .gz file")

    test_database = "buyhouse_restore_check_" + datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")
    if not DATABASE_PATTERN.fullmatch(test_database):
        raise SystemExit("invalid generated test database name")
    option_path: Path | None = None
    created = False
    phase = "prepare"
    try:
        option_path = create_option_file()
        phase = "create_test_database"
        execute_or_raise(
            option_path,
            ["-e", f"CREATE DATABASE `{test_database}` CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci"],
        )
        created = True
        phase = "import_backup"
        restore_backup_or_raise(option_path, test_database, backup)
        phase = "count_tables"
        result = execute_or_raise(
            option_path,
            [
                "--batch",
                "--skip-column-names",
                "-e",
                "SELECT COUNT(*) FROM information_schema.tables "
                f"WHERE table_schema = '{test_database}'",
            ],
        )
        table_count = int(result.stdout.decode("utf-8").strip())
        if table_count < 1:
            raise RuntimeError("temporary restore contains no tables")
        print(f"restore_verification=passed")
        print(f"restored_table_count={table_count}")
        print(f"backup_file={backup.name}")
        return 0
    except Exception as exc:
        print("restore_verification=failed:" + phase + ":" + str(exc), file=sys.stderr)
        return 1
    finally:
        if created and option_path and not args.keep_test_database:
            mysql_command(option_path, ["-e", f"DROP DATABASE IF EXISTS `{test_database}`"])
        if option_path and option_path.exists():
            option_path.unlink()


if __name__ == "__main__":
    sys.exit(main())
