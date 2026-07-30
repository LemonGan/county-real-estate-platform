#!/usr/bin/env python3
"""Create a credential-safe logical MySQL backup for the BuyHouse API.

Run from the backend directory so the protected .env file is loaded by the
application configuration. Credentials are written only to a mode-600 temporary
MySQL option file and removed before the command exits.
"""
from __future__ import annotations

import argparse
import gzip
import os
import re
import shutil
import subprocess
import sys
import tempfile
from datetime import datetime, timedelta, timezone
from pathlib import Path
from urllib.parse import unquote, urlsplit

BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from app.core.config import settings

FILENAME_PATTERN = re.compile(r"^buyhouse_mysql_\d{8}T\d{6}Z\.sql\.gz$")
DATABASE_PATTERN = re.compile(r"^[A-Za-z0-9_]+$")


def option_value(value: str) -> str:
    if "\n" in value or "\r" in value:
        raise ValueError("database connection value contains a newline")
    return '"' + value.replace("\\", "\\\\").replace('"', '\\"') + '"'


def mysql_connection() -> tuple[str, int, str, str, str]:
    parsed = urlsplit(settings.DATABASE_URL)
    if not parsed.scheme.startswith("mysql"):
        raise ValueError("DATABASE_URL is not a MySQL connection string")
    database = parsed.path.lstrip("/").split("/", 1)[0]
    if not DATABASE_PATTERN.fullmatch(database):
        raise ValueError("database name contains unsupported characters")
    if not parsed.username or parsed.password is None:
        raise ValueError("DATABASE_URL is missing database credentials")
    return (
        parsed.hostname or "localhost",
        parsed.port or 3306,
        unquote(parsed.username),
        unquote(parsed.password),
        database,
    )


def remove_expired_backups(directory: Path, retention_days: int) -> int:
    cutoff = datetime.now(timezone.utc) - timedelta(days=retention_days)
    removed = 0
    for path in directory.iterdir():
        if not path.is_file() or not FILENAME_PATTERN.fullmatch(path.name):
            continue
        modified = datetime.fromtimestamp(path.stat().st_mtime, tz=timezone.utc)
        if modified < cutoff:
            path.unlink()
            removed += 1
    return removed


def main() -> int:
    parser = argparse.ArgumentParser(description="Create BuyHouse MySQL backup")
    parser.add_argument("--output-dir", default="/www/backup/database/buyhouse")
    parser.add_argument("--retention-days", type=int, default=14)
    args = parser.parse_args()
    if args.retention_days < 1:
        raise SystemExit("retention days must be at least 1")

    output_dir = Path(args.output_dir)
    output_dir.mkdir(mode=0o750, parents=True, exist_ok=True)
    output_dir.chmod(0o750)
    host, port, user, password, database = mysql_connection()

    option_path: Path | None = None
    raw_path: Path | None = None
    target_path: Path | None = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w", encoding="utf-8", prefix="buyhouse-mysql-", suffix=".cnf", delete=False
        ) as option_file:
            option_path = Path(option_file.name)
            os.chmod(option_path, 0o600)
            option_file.write(
                "[client]\n"
                f"host={option_value(host)}\n"
                f"port={port}\n"
                f"user={option_value(user)}\n"
                f"password={option_value(password)}\n"
            )

        stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        target_path = output_dir / f"buyhouse_mysql_{stamp}.sql.gz"
        raw_path = output_dir / f".buyhouse_mysql_{stamp}.sql.tmp"
        command = [
            "mysqldump",
            f"--defaults-extra-file={option_path}",
            "--single-transaction",
            "--quick",
            "--routines",
            "--events",
            "--triggers",
            "--set-gtid-purged=OFF",
            database,
        ]
        with raw_path.open("wb") as raw_file:
            completed = subprocess.run(command, stdout=raw_file, stderr=subprocess.PIPE, check=False)
        if completed.returncode != 0:
            raise RuntimeError("mysqldump failed without creating a usable backup")

        with raw_path.open("rb") as raw_file, gzip.open(target_path, "wb", compresslevel=6) as archive:
            shutil.copyfileobj(raw_file, archive)
        os.chmod(target_path, 0o640)
        raw_path.unlink()
        raw_path = None
        removed = remove_expired_backups(output_dir, args.retention_days)
        print(f"backup_file={target_path.name}")
        print(f"backup_size_bytes={target_path.stat().st_size}")
        print(f"expired_backups_removed={removed}")
        return 0
    except Exception as exc:
        if target_path and target_path.exists():
            target_path.unlink()
        print(f"backup_failed={type(exc).__name__}", file=sys.stderr)
        return 1
    finally:
        if raw_path and raw_path.exists():
            raw_path.unlink()
        if option_path and option_path.exists():
            option_path.unlink()


if __name__ == "__main__":
    sys.exit(main())
