
import re
import time
import sqlite3

from database.connection import connect_db


def execute_query(query):
    """Execute a read-only SELECT query using SQLXpert's SQLite database."""

    if not isinstance(query, str) or not query.strip():
        return {
            "success": False,
            "message": "Please enter a SQL query."
        }

    cleaned = re.sub(
        r"--[^\n]*|/\*[\s\S]*?\*/",
        "",
        query
    ).strip()

    if not re.match(r"(?is)^SELECT\b", cleaned):
        return {
            "success": False,
            "message": "Only SELECT queries are allowed in this module."
        }

    statement = cleaned[:-1] if cleaned.endswith(";") else cleaned

    if ";" in statement:
        return {
            "success": False,
            "message": "Multiple SQL statements are not allowed."
        }

    forbidden = re.compile(
        r"\b(INSERT|UPDATE|DELETE|DROP|ALTER|CREATE|ATTACH|"
        r"DETACH|PRAGMA|REPLACE|VACUUM)\b",
        re.IGNORECASE
    )

    if forbidden.search(statement):
        return {
            "success": False,
            "message": "A non-read-only SQL operation was detected."
        }

    connection = None
    start = time.perf_counter()

    try:
        connection = connect_db()

        # Interrupt long-running queries after approximately 1.5 seconds.
        connection.set_progress_handler(
            lambda: int(time.perf_counter() - start > 1.5),
            10000
        )

        cursor = connection.execute(query)
        rows = cursor.fetchmany(201)

        if len(rows) > 200:
            rows = rows[:200]

        columns = [
            description[0]
            for description in (cursor.description or [])
        ]

        elapsed_ms = round(
            (time.perf_counter() - start) * 1000,
            2
        )

        return {
            "success": True,
            "message": "Query executed successfully.",
            "columns": columns,
            "rows": [dict(row) for row in rows],
            "row_count": len(rows),
            "execution_time_ms": elapsed_ms
        }

    except sqlite3.Error as error:
        return {
            "success": False,
            "message": "Query execution failed.",
            "error": str(error)
        }

    finally:
        if connection is not None:
            connection.close()
