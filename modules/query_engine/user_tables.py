
import re
import sqlite3
from pathlib import Path

from flask import Blueprint, request, jsonify

user_tables_bp = Blueprint("user_tables", __name__)

# Change this path if your application uses a different database file.
DB_PATH = Path(__file__).resolve().parents[2] / "sqlxpert.db"

IDENTIFIER = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")

ALLOWED_TYPES = {
    "TEXT", "INTEGER", "REAL", "BLOB",
    "NUMERIC", "INTEGER PRIMARY KEY",
    "INTEGER PRIMARY KEY AUTOINCREMENT"
}


def get_connection():
    connection = sqlite3.connect(DB_PATH)
    connection.row_factory = sqlite3.Row
    return connection


def valid_identifier(name):
    return isinstance(name, str) and bool(IDENTIFIER.fullmatch(name))


def table_exists(connection, table_name):
    result = connection.execute(
        "SELECT 1 FROM sqlite_master "
        "WHERE type = 'table' AND name = ?",
        (table_name,)
    ).fetchone()
    return result is not None


def get_columns(connection, table_name):
    if not valid_identifier(table_name):
        raise ValueError("Invalid table name.")

    if not table_exists(connection, table_name):
        raise ValueError("Table does not exist.")

    return [
        row["name"]
        for row in connection.execute(
            f'PRAGMA table_info("{table_name}")'
        ).fetchall()
    ]


@user_tables_bp.get("/api/user-tables")
def list_user_tables():
    with get_connection() as connection:
        rows = connection.execute("""
            SELECT name FROM sqlite_master
            WHERE type = 'table'
              AND name NOT LIKE 'sqlite_%'
            ORDER BY name
        """).fetchall()

    return jsonify({"tables": [row["name"] for row in rows]})


@user_tables_bp.post("/api/user-tables")
def create_user_table():
    data = request.get_json(silent=True) or {}
    table_name = data.get("table_name")
    columns = data.get("columns")

    if not valid_identifier(table_name):
        return jsonify({
            "error": "Enter a valid table name."
        }), 400

    if not isinstance(columns, list) or not columns:
        return jsonify({
            "error": "Add at least one column."
        }), 400

    definitions = []
    seen = set()

    for column in columns:
        if not isinstance(column, dict):
            return jsonify({"error": "Invalid column definition."}), 400

        name = column.get("name")
        column_type = str(column.get("type", "TEXT")).upper()

        if not valid_identifier(name):
            return jsonify({"error": f"Invalid column name: {name}"}), 400

        if name.lower() in seen:
            return jsonify({"error": f"Duplicate column: {name}"}), 400

        if column_type not in ALLOWED_TYPES:
            return jsonify({"error": f"Unsupported type: {column_type}"}), 400

        seen.add(name.lower())
        definitions.append(f'"{name}" {column_type}')

    sql = (
        f'CREATE TABLE "{table_name}" '
        f'({", ".join(definitions)})'
    )

    try:
        with get_connection() as connection:
            if table_exists(connection, table_name):
                return jsonify({"error": "That table already exists."}), 409

            connection.execute(sql)

        return jsonify({
            "message": f"Table '{table_name}' created successfully."
        }), 201

    except sqlite3.Error as error:
        return jsonify({"error": str(error)}), 400


@user_tables_bp.post("/api/user-tables/<table_name>/records")
def insert_user_record(table_name):
    data = request.get_json(silent=True) or {}
    values = data.get("values")

    if not valid_identifier(table_name):
        return jsonify({"error": "Invalid table name."}), 400

    if not isinstance(values, dict) or not values:
        return jsonify({"error": "Provide record values."}), 400

    try:
        with get_connection() as connection:
            columns = get_columns(connection, table_name)

            if not all(
                isinstance(name, str) and name in columns
                for name in values
            ):
                return jsonify({
                    "error": "One or more columns do not exist."
                }), 400

            names = list(values.keys())
            placeholders = ", ".join("?" for _ in names)
            quoted_names = ", ".join(f'"{name}"' for name in names)

            sql = (
                f'INSERT INTO "{table_name}" '
                f'({quoted_names}) VALUES ({placeholders})'
            )

            connection.execute(
                sql, [values[name] for name in names]
            )

        return jsonify({"message": "Record inserted successfully."}), 201

    except (sqlite3.Error, ValueError) as error:
        return jsonify({"error": str(error)}), 400


@user_tables_bp.get("/api/user-tables/<table_name>/records")
def list_user_records(table_name):
    try:
        with get_connection() as connection:
            get_columns(connection, table_name)

            rows = connection.execute(
                f'SELECT * FROM "{table_name}" LIMIT 500'
            ).fetchall()

            return jsonify({
                "columns": get_columns(connection, table_name),
                "records": [dict(row) for row in rows]
            })

    except (sqlite3.Error, ValueError) as error:
        return jsonify({"error": str(error)}), 400


@user_tables_bp.post("/api/user-query")
def execute_user_query():
    data = request.get_json(silent=True) or {}
    sql = data.get("sql", "").strip()

    if not sql:
        return jsonify({"error": "Enter a SQL query."}), 400

    # This endpoint accepts one statement at a time.
    statement = sql.rstrip().rstrip(";").strip()

    if ";" in statement:
        return jsonify({
            "error": "Execute one SQL statement at a time."
        }), 400

    first_word = statement.split(None, 1)[0].upper()

    # Do not allow database administration or schema deletion here.
    if first_word not in {"SELECT", "INSERT", "UPDATE", "DELETE"}:
        return jsonify({
            "error": "Use SELECT, INSERT, UPDATE, or DELETE here. "
                     "Create tables using the table builder."
        }), 400

    try:
        with get_connection() as connection:
            cursor = connection.execute(statement)

            if first_word == "SELECT":
                rows = cursor.fetchmany(500)
                return jsonify({
                    "columns": [
                        item[0] for item in (cursor.description or [])
                    ],
                    "rows": [dict(row) for row in rows],
                    "limited": len(rows) == 500
                })

            affected = cursor.rowcount

        return jsonify({
            "message": "Query executed successfully.",
            "affected_rows": affected
        })

    except sqlite3.Error as error:
        return jsonify({"error": str(error)}), 400
