import re

from .lexer import tokenize
from .parser import parse_sql, SQLSyntaxError


def _normalize_schema(schema):
    normalized = {}

    if not schema:
        return normalized

    for table_name, columns in schema.items():
        table_name = str(table_name).lower()
        normalized[table_name] = set()

        for column in columns:
            if isinstance(column, dict):
                column_name = column.get("name", "")
            else:
                column_name = str(column)

            if column_name:
                normalized[table_name].add(column_name.lower())

    return normalized


def _diagnostic(stage, message, token=None):
    return {
        "stage": stage,
        "message": message,
        "line": token.get("line", 1) if token else 1,
        "column": token.get("column", 1) if token else 1,
    }


def _semantic_check(ast, schema, diagnostics):
    if not ast:
        return

    schema = _normalize_schema(schema)
    statement_type = ast.get("type", "")

    if statement_type == "SelectStatement":
        tables = ast.get("tables", [])
        known_tables = set()

        for table in tables:
            table_name = table.get("name", "").lower()

            if not table_name:
                continue

            if schema and table_name not in schema:
                diagnostics.append(
                    _diagnostic(
                        "semantic",
                        f"Table '{table_name}' does not exist."
                    )
                )
            else:
                known_tables.add(table_name)

        if not schema:
            return

        select_items = ast.get("select", [])

        for item in select_items:
            if not isinstance(item, str):
                continue

            item = item.strip()

            if item == "*" or "(" in item:
                continue

            if "." in item:
                parts = item.split(".", 1)
                qualifier = parts[0].strip().lower()
                column_name = parts[1].strip().lower()

                matching_table = None

                for table in tables:
                    table_name = table.get("name", "").lower()
                    alias = table.get("alias", "").lower()

                    if qualifier == table_name or qualifier == alias:
                        matching_table = table_name
                        break

                if matching_table:
                    if (
                        matching_table in schema
                        and column_name not in schema[matching_table]
                    ):
                        diagnostics.append(
                            _diagnostic(
                                "semantic",
                                f"Column '{column_name}' does not exist "
                                f"in table '{matching_table}'."
                            )
                        )
                elif qualifier not in {
                    table.get("alias", "").lower()
                    for table in tables
                }:
                    diagnostics.append(
                        _diagnostic(
                            "semantic",
                            f"Unknown table or alias '{qualifier}'."
                        )
                    )

            else:
                column_name = item.lower()

                matching_tables = [
                    table_name
                    for table_name in known_tables
                    if column_name in schema.get(table_name, set())
                ]

                if not matching_tables:
                    diagnostics.append(
                        _diagnostic(
                            "semantic",
                            f"Column '{column_name}' does not exist "
                            "in the referenced tables."
                        )
                    )

    elif statement_type == "InsertStatement":
        table_name = ast.get("table", "").lower()

        if schema and table_name not in schema:
            diagnostics.append(
                _diagnostic(
                    "semantic",
                    f"Table '{table_name}' does not exist."
                )
            )
            return

        columns = ast.get("columns", [])
        values = ast.get("values", [])

        if columns and values and len(columns) != len(values):
            diagnostics.append(
                _diagnostic(
                    "semantic",
                    "The number of INSERT columns does not match "
                    "the number of values."
                )
            )

        if schema and table_name in schema:
            for column in columns:
                column_name = str(column).lower()

                if column_name not in schema[table_name]:
                    diagnostics.append(
                        _diagnostic(
                            "semantic",
                            f"Column '{column_name}' does not exist "
                            f"in table '{table_name}'."
                        )
                    )

    elif statement_type == "CreateTableStatement":
        table_name = ast.get("table", "").lower()

        if schema and table_name in schema:
            diagnostics.append(
                _diagnostic(
                    "semantic",
                    f"Table '{table_name}' already exists."
                )
            )


def analyze(sql, schema=None):
    diagnostics = []
    tokens = []
    ast = None

    if not isinstance(sql, str) or not sql.strip():
        diagnostics.append(
            _diagnostic("syntax", "SQL query cannot be empty.")
        )
        return {
            "tokens": tokens,
            "ast": ast,
            "diagnostics": diagnostics,
            "success": False,
        }

    try:
        tokens = tokenize(sql)
    except (ValueError, SyntaxError) as error:
        diagnostics.append(
            _diagnostic("lexical", str(error))
        )

        return {
            "tokens": tokens,
            "ast": ast,
            "diagnostics": diagnostics,
            "success": False,
        }

    try:
        ast = parse_sql(tokens)
    except SQLSyntaxError as error:
        diagnostics.append({
            "stage": "syntax",
            "message": error.message,
            "line": error.line,
            "column": error.column,
        })
    except (ValueError, IndexError) as error:
        diagnostics.append(
            _diagnostic("syntax", str(error))
        )

    if ast is not None:
        _semantic_check(ast, schema, diagnostics)

    return {
        "tokens": tokens,
        "ast": ast,
        "diagnostics": diagnostics,
        "success": len(diagnostics) == 0,
    }