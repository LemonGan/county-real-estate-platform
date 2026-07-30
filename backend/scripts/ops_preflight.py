#!/usr/bin/env python3
"""Production preflight for the BuyHouse API.

This script is intentionally read-only: it never reads application credentials,
changes service state, creates backups, or deletes files.
"""
from __future__ import annotations

import argparse
import json
import shutil
import sys
import urllib.error
import urllib.request
from pathlib import Path


def check_http(url: str, timeout: int) -> dict:
    try:
        with urllib.request.urlopen(url, timeout=timeout) as response:
            body = json.loads(response.read().decode("utf-8"))
        healthy = response.status == 200 and body.get("status") == "healthy"
        return {
            "name": "api_health",
            "ok": healthy,
            "detail": f"HTTP {response.status}",
        }
    except (urllib.error.URLError, TimeoutError, ValueError) as exc:
        return {"name": "api_health", "ok": False, "detail": str(exc)}


def check_disk(path: Path, warning_percent: int, critical_percent: int) -> dict:
    usage = shutil.disk_usage(path)
    free_percent = round(usage.free / usage.total * 100, 1)
    if free_percent <= critical_percent:
        level = "critical"
    elif free_percent <= warning_percent:
        level = "warning"
    else:
        level = "ok"
    return {
        "name": "disk_space",
        "ok": level == "ok",
        "level": level,
        "path": str(path),
        "free_gb": round(usage.free / 1024**3, 2),
        "free_percent": free_percent,
    }


def directory_size(path: Path) -> int:
    if not path.exists():
        return 0
    return sum(
        entry.stat().st_size
        for entry in path.rglob("*")
        if entry.is_file() and not entry.is_symlink()
    )


def check_backup_size(path: Path) -> dict:
    return {
        "name": "backup_inventory",
        "ok": True,
        "path": str(path),
        "size_gb": round(directory_size(path) / 1024**3, 2),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Read-only production health preflight")
    parser.add_argument("--health-url", default="http://127.0.0.1:8000/health")
    parser.add_argument("--disk-path", default="/www")
    parser.add_argument("--backup-path", default="/www/backup")
    parser.add_argument("--warning-free-percent", type=int, default=15)
    parser.add_argument("--critical-free-percent", type=int, default=10)
    parser.add_argument("--timeout", type=int, default=10)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    checks = [
        check_http(args.health_url, args.timeout),
        check_disk(Path(args.disk_path), args.warning_free_percent, args.critical_free_percent),
        check_backup_size(Path(args.backup_path)),
    ]
    success = all(check["ok"] for check in checks)
    result = {"ok": success, "checks": checks}

    if args.json:
        print(json.dumps(result, ensure_ascii=False))
    else:
        for check in checks:
            level = check.get("level", "ok" if check["ok"] else "error")
            detail = ", ".join(
                f"{key}={value}"
                for key, value in check.items()
                if key not in {"name", "ok", "level"}
            )
            print(f"[{level.upper()}] {check['name']}: {detail}")
    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())
