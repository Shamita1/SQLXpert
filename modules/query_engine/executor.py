import sqlite3
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DB_PATH = PROJECT_ROOT / "sqlxpert.db"


def execute_query(sql, params=()):
    """Execute a SQL query and return columns and rows."""
    if not isinstance(sql, str) or not sql.strip():
        raise ValueError("Please enter a SQL query.")

    connection = sqlite3.connect(DB_PATH)
    connection.row_factory = sqlite3.Row

    try:
        cursor = connection.execute(sql, params)

        if cursor.description is None:
            connection.commit()
            return {
                "columns": [],
                "rows": [],
                "message": "Query executed successfully.",
            }

        columns = [column[0] for column in cursor.description]
        rows = [dict(row) for row in cursor.fetchall()]

        return {
            "columns": columns,
            "rows": rows,
            "message": "Query executed successfully.",
        }
    finally:
        connection.close()