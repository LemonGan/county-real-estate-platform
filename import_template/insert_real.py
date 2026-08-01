"""Import real-estate seed data using environment variables.

This script intentionally contains no credentials. Set these variables before use:

- BUYHOUSE_DB_HOST
- BUYHOUSE_DB_PORT
- BUYHOUSE_DB_USER
- BUYHOUSE_DB_PASSWORD
- BUYHOUSE_DB_NAME
"""
import os

import pymysql


def connect():
    return pymysql.connect(
        host=os.environ.get("BUYHOUSE_DB_HOST", "127.0.0.1"),
        port=int(os.environ.get("BUYHOUSE_DB_PORT", "3306")),
        user=os.environ["BUYHOUSE_DB_USER"],
        password=os.environ["BUYHOUSE_DB_PASSWORD"],
        database=os.environ["BUYHOUSE_DB_NAME"],
        charset="utf8mb4",
    )


if __name__ == "__main__":
    raise SystemExit("Set DB env vars and extend this template with an explicit import routine before running.")
