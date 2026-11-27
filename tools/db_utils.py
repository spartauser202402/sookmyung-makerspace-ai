"""
db_utils.py — 공유 DB 연결 헬퍼 (모든 Tool에서 import)
절대 학번/비밀번호를 받거나 저장하지 않음.
"""
import sqlite3
import os
from pathlib import Path

# DB 파일은 프로젝트 루트의 db/ 아래
_DB_PATH = Path(__file__).resolve().parent.parent / "db" / "makerspace.db"


def get_connection() -> sqlite3.Connection:
    """Return a SQLite connection with row_factory and FK enforcement."""
    if not _DB_PATH.exists():
        raise FileNotFoundError(
            f"DB not found at {_DB_PATH}. Run `python db/seed.py` first."
        )
    conn = sqlite3.connect(str(_DB_PATH))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys=ON")
    return conn
