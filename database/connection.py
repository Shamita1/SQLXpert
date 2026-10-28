
import sqlite3

from config import DATABASE_PATH


def connect_db():
    """Open a connection to SQLXpert's shared SQLite database."""
    conn = sqlite3.connect(DATABASE_PATH, timeout=5)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn
