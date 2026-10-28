import sqlite3


BLOCKED_KEYWORDS = {
    "ATTACH",
    "DETACH",
    "DROP",
    "ALTER",
    "TRUNCATE",
    "VACUUM",
}


def validate_query(sql):
    """Validate a single SQL statement before execution."""
    if not isinstance(sql, str) or not sql.strip():
        raise ValueError("Please enter a SQL query.")

    statements = [
        statement.strip()
        for statement in sql.strip().split(";")
        if statement.strip()
    ]

    if len(statements) != 1:
        raise ValueError("Please execute one SQL statement at a time.")

    statement = statements[0]
    first_keyword = statement.split(maxsplit=1)[0].upper()

    if first_keyword in BLOCKED_KEYWORDS:
        raise ValueError(
            f"The SQL command '{first_keyword}' is not allowed."
        )

    try:
        sqlite3.complete_statement(statement + ";")
    except sqlite3.Error as error:
        raise ValueError(f"Invalid SQL statement: {error}") from error

    return True