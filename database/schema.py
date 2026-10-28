
from database.connection import connect_db


INTERNAL_TABLES = {
    "query_history",
    "challenge_attempts",
}


def schema_info():
    """Return user-visible tables and their column metadata."""
    conn = connect_db()

    try:
        tables = {}

        rows = conn.execute(
            """
            SELECT name
            FROM sqlite_master
            WHERE type = 'table'
              AND name NOT LIKE 'sqlite_%'
            ORDER BY name
            """
        ).fetchall()

        for row in rows:
            table_name = row["name"]

            if table_name in INTERNAL_TABLES:
                continue

            # Table names originate from sqlite_master, not user input.
            escaped_name = table_name.replace("'", "''")

            columns = conn.execute(
                f"PRAGMA table_info('{escaped_name}')"
            ).fetchall()

            tables[table_name] = [
                dict(column) for column in columns
            ]

        return tables

    finally:
        conn.close()
