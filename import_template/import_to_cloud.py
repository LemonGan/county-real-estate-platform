"""Cloud import helper template.

No credentials or server IPs are stored in this file. Configure runtime connection
settings through environment variables or a local, ignored config file.
"""
import os

DB_CONFIG = {
    "host": os.environ.get("BUYHOUSE_DB_HOST", "127.0.0.1"),
    "port": int(os.environ.get("BUYHOUSE_DB_PORT", "3306")),
    "user": os.environ.get("BUYHOUSE_DB_USER", ""),
    "password": os.environ.get("BUYHOUSE_DB_PASSWORD", ""),
    "database": os.environ.get("BUYHOUSE_DB_NAME", ""),
    "charset": "utf8mb4",
}


if __name__ == "__main__":
    raise SystemExit("This is a credential-free template. Provide env vars and implement the import step explicitly.")
