
import sqlite3
from .problem_bank import CHALLENGES

def evaluate_submission(challenge_id, user_sql):
    """Execute a challenge submission and compare its output."""

    challenge = next(
        (item for item in CHALLENGES if item["id"] == challenge_id),
        None
    )

    if challenge is None:
        return {
            "success": False,
            "correct": False,
            "feedback": "Challenge not found.",
            "score": 0,
            "columns": [],
            "rows": [],
        }

    if not user_sql or not user_sql.strip():
        return {
            "success": False,
            "correct": False,
            "feedback": "Please enter an SQL query.",
            "score": 0,
            "columns": [],
            "rows": [],
        }

    # Allow only a single read-only SELECT statement.
    sql = user_sql.strip()

    if sql.endswith(";"):
        sql = sql[:-1].strip()

    if ";" in sql:
        return _error("Only one SQL statement is allowed.")

    if not sql.lower().startswith("select"):
        return _error("Only SELECT queries are allowed in challenges.")

    connection = sqlite3.connect(":memory:")

    try:
        cursor = connection.cursor()

        # Create fresh sample tables for this submission.
        cursor.executescript(challenge["setup_sql"])

        # SQLite's authorizer blocks data changes and schema changes.
        def authorize(action, arg1, arg2, database, trigger):
            allowed = {
                sqlite3.SQLITE_SELECT,
                sqlite3.SQLITE_READ,
                sqlite3.SQLITE_FUNCTION,
                sqlite3.SQLITE_RECURSIVE,
            }
            if action in allowed:
                return sqlite3.SQLITE_OK
            return sqlite3.SQLITE_DENY

        connection.set_authorizer(authorize)

        cursor.execute(sql)
        columns = [item[0] for item in cursor.description or []]
        rows = cursor.fetchall()

        # Run the official answer on a separate fresh database.
        expected_connection = sqlite3.connect(":memory:")
        try:
            expected_cursor = expected_connection.cursor()
            expected_cursor.executescript(challenge["setup_sql"])
            expected_cursor.execute(challenge["solution_sql"])

            expected_columns = [
                item[0] for item in expected_cursor.description or []
            ]
            expected_rows = expected_cursor.fetchall()
        finally:
            expected_connection.close()

        # Compare column names and values, ignoring row order.
        actual = (columns, sorted(map(repr, rows)))
        expected = (expected_columns, sorted(map(repr, expected_rows)))
        correct = actual == expected

        return {
            "success": True,
            "correct": correct,
            "feedback": (
                "Correct! Well done."
                if correct
                else "The query ran, but its output does not match the expected result."
            ),
            "score": challenge["points"] if correct else 0,
            "max_score": challenge["points"],
            "columns": columns,
            "rows": rows,
        }

    except sqlite3.Error as error:
        return _error(f"SQL error: {error}")

    finally:
        connection.close()


def _error(message):
    return {
        "success": False,
        "correct": False,
        "feedback": message,
        "score": 0,
        "max_score": 0,
        "columns": [],
        "rows": [],
    }
