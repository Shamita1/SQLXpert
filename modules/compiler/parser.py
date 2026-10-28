
from .lexer import tokenize


CLAUSE_ORDER = {
    "WHERE": 1,
    "GROUP": 2,
    "HAVING": 3,
    "ORDER": 4,
    "LIMIT": 5,
    "OFFSET": 6
}


class SQLSyntaxError(Exception):
    """Raised when the SQL structure is invalid."""

    def __init__(self, message, line=1, column=1):
        super().__init__(message)
        self.message = message
        self.line = line
        self.column = column


def _error(message, token=None):
    token = token or {"line": 1, "column": 1}
    raise SQLSyntaxError(
        message,
        token.get("line", 1),
        token.get("column", 1)
    )


def _is_identifier(token):
    return token["type"] == "IDENTIFIER"


def _top_level_keyword(tokens, keyword, start=0):
    """Find a keyword outside parentheses."""
    depth = 0

    for i in range(start, len(tokens)):
        value = tokens[i]["value"].upper()

        if value == "(":
            depth += 1
        elif value == ")":
            depth -= 1
        elif depth == 0 and value == keyword:
            return i

    return None


def _split_top_level(tokens):
    """Split tokens at commas that are outside parentheses."""
    parts = []
    current = []
    depth = 0

    for token in tokens:
        value = token["value"]

        if value == "(":
            depth += 1
        elif value == ")":
            depth -= 1

        if value == "," and depth == 0:
            if not current:
                _error("Unexpected comma.", token)

            parts.append(current)
            current = []
        else:
            current.append(token)

    if not current and parts:
        _error("Expected an expression after the comma.")

    if current:
        parts.append(current)

    return parts


def _check_parentheses(tokens):
    stack = []

    for token in tokens:
        value = token["value"]

        if value == "(":
            stack.append(token)
        elif value == ")":
            if not stack:
                _error("Unexpected closing parenthesis.", token)
            stack.pop()

    if stack:
        _error("Missing closing parenthesis.", stack[-1])


def _remove_final_semicolon(tokens):
    """Allow one final semicolon, but no multiple statements."""
    semicolons = [
        i for i, token in enumerate(tokens)
        if token["value"] == ";"
    ]

    if not semicolons:
        return tokens

    if len(semicolons) != 1 or semicolons[0] != len(tokens) - 1:
        _error(
            "Only one SQL statement is allowed at a time.",
            tokens[semicolons[0]]
        )

    return tokens[:-1]


def _table_reference(tokens, index):
    if index >= len(tokens) or not _is_identifier(tokens[index]):
        _error("Expected a table name.", tokens[index] if index < len(tokens) else None)

    table_name = tokens[index]["value"]
    index += 1
    alias = table_name

    # Optional explicit AS alias.
    if index < len(tokens) and tokens[index]["value"].upper() == "AS":
        index += 1

        if index >= len(tokens) or not _is_identifier(tokens[index]):
            _error("Expected an alias after AS.", tokens[index] if index < len(tokens) else None)

        alias = tokens[index]["value"]
        index += 1

    # Optional implicit alias.
    elif index < len(tokens) and _is_identifier(tokens[index]):
        if tokens[index]["value"].upper() not in {
            "WHERE", "JOIN", "INNER", "LEFT", "RIGHT", "FULL",
            "CROSS", "ON", "GROUP", "ORDER", "HAVING", "LIMIT",
            "OFFSET"
        }:
            alias = tokens[index]["value"]
            index += 1

    return {
        "name": table_name,
        "alias": alias
    }, index


def _parse_select(tokens):
    if len(tokens) < 4:
        _error("Incomplete SELECT statement.", tokens[0])

    if tokens[0]["value"].upper() != "SELECT":
        _error("A SELECT statement must begin with SELECT.", tokens[0])

    from_index = _top_level_keyword(tokens, "FROM", 1)

    if from_index is None:
        _error("Missing FROM clause.", tokens[0])

    select_tokens = tokens[1:from_index]

    if not select_tokens:
        _error("SELECT must contain at least one column or expression.", tokens[0])

    if select_tokens[-1]["value"] == ",":
        _error("Expected a column after the comma.", select_tokens[-1])

    if select_tokens[0]["value"] == ",":
        _error("Unexpected comma in SELECT list.", select_tokens[0])

    # A simple guard against common clause-order mistakes.
    last_order = 0

    for i, token in enumerate(tokens):
        value = token["value"].upper()

        if value == "GROUP" and i + 1 < len(tokens):
            if tokens[i + 1]["value"].upper() == "BY":
                order = CLAUSE_ORDER["GROUP"]
            else:
                continue
        elif value == "ORDER" and i + 1 < len(tokens):
            if tokens[i + 1]["value"].upper() == "BY":
                order = CLAUSE_ORDER["ORDER"]
            else:
                continue
        elif value in CLAUSE_ORDER:
            order = CLAUSE_ORDER[value]
        else:
            continue

        if order < last_order:
            _error(f"Unexpected clause {value}. Check the SQL clause order.", token)

        last_order = order

    # Find the end of the FROM section.
    clause_positions = []

    for keyword in ("WHERE", "GROUP", "HAVING", "ORDER", "LIMIT", "OFFSET"):
        index = _top_level_keyword(tokens, keyword, from_index + 1)

        if index is not None:
            # GROUP BY and ORDER BY must be treated as paired clauses.
            if keyword in ("GROUP", "ORDER"):
                if index + 1 >= len(tokens) or tokens[index + 1]["value"].upper() != "BY":
                    continue

            clause_positions.append((index, keyword))

    clause_positions.sort()
    from_end = clause_positions[0][0] if clause_positions else len(tokens)

    from_tokens = tokens[from_index + 1:from_end]

    if not from_tokens:
        _error("FROM must be followed by a table name.", tokens[from_index])

    # Extract tables from FROM and JOIN sections.
    tables = []
    i = 0
    expect_table = True

    while i < len(from_tokens):
        token = from_tokens[i]
        value = token["value"].upper()

        if value == ",":
            expect_table = True
            i += 1
            continue

        if value in ("JOIN", "INNER", "LEFT", "RIGHT", "FULL", "CROSS"):
            if value != "JOIN" and i + 1 < len(from_tokens):
                next_value = from_tokens[i + 1]["value"].upper()
                if next_value in ("OUTER", "JOIN"):
                    i += 1
                    continue

            if value == "JOIN":
                expect_table = True
                i += 1
                continue

        if value == "ON" or value == "USING":
            expect_table = False
            i += 1
            continue

        if expect_table:
            table, i = _table_reference(from_tokens, i)
            tables.append(table)
            expect_table = False
        else:
            i += 1

    if not tables:
        _error("Could not identify a source table.", tokens[from_index])

    clauses = {}

    for index, keyword in clause_positions:
        if keyword == "GROUP":
            start = index + 2
        elif keyword == "ORDER":
            start = index + 2
        else:
            start = index + 1

        later = [
            pos for pos, _ in clause_positions if pos > index
        ]
        end = min(later) if later else len(tokens)

        expression = tokens[start:end]

        if not expression:
            _error(f"{keyword} clause is incomplete.", tokens[index])

        clauses[keyword] = [t["value"] for t in expression]

    return {
        "type": "SelectStatement",
        "select": [t["value"] for t in select_tokens],
        "from": tables[0]["name"],
        "tables": tables,
        "clauses": clauses
    }


def _parse_create(tokens):
    if len(tokens) < 5:
        _error("Incomplete CREATE TABLE statement.", tokens[0])

    if tokens[1]["value"].upper() != "TABLE":
        _error("Only CREATE TABLE is supported.", tokens[1])

    i = 2

    if i + 2 < len(tokens):
        if (
            tokens[i]["value"].upper() == "IF"
            and tokens[i + 1]["value"].upper() == "NOT"
            and tokens[i + 2]["value"].upper() == "EXISTS"
        ):
            i += 3

    if i >= len(tokens) or not _is_identifier(tokens[i]):
        _error("Expected a table name after CREATE TABLE.", tokens[i] if i < len(tokens) else None)

    table_name = tokens[i]["value"]
    i += 1

    if i >= len(tokens) or tokens[i]["value"] != "(":
        _error("Expected '(' after the table name.", tokens[i] if i < len(tokens) else None)

    _check_parentheses(tokens[i:])

    if tokens[-1]["value"] != ")":
        _error("Expected ')' at the end of the column definitions.", tokens[-1])

    definitions = _split_top_level(tokens[i + 1:-1])

    if not definitions:
        _error("A table must contain at least one column.", tokens[i])

    columns = []

    for definition in definitions:
        if len(definition) < 2 or not _is_identifier(definition[0]):
            _error("Each column needs a name and a data type.", definition[0] if definition else tokens[i])

        columns.append({
            "name": definition[0]["value"],
            "definition": [t["value"] for t in definition[1:]]
        })

    return {
        "type": "CreateTableStatement",
        "table": table_name,
        "columns": columns
    }


def _parse_insert(tokens):
    if len(tokens) < 6 or tokens[1]["value"].upper() != "INTO":
        _error("Use INSERT INTO table_name VALUES (...).", tokens[0])

    if not _is_identifier(tokens[2]):
        _error("Expected a table name after INSERT INTO.", tokens[2])

    table_name = tokens[2]["value"]
    i = 3
    columns = []

    if i < len(tokens) and tokens[i]["value"] == "(":
        close = next(
            (j for j in range(i, len(tokens)) if tokens[j]["value"] == ")"),
            None
        )

        if close is None:
            _error("Missing ')' in the INSERT column list.", tokens[i])

        columns = [
            part[0]["value"]
            for part in _split_top_level(tokens[i + 1:close])
            if part
        ]
        i = close + 1

    if i >= len(tokens) or tokens[i]["value"].upper() != "VALUES":
        _error("INSERT must contain a VALUES clause.", tokens[i] if i < len(tokens) else None)

    i += 1

    if i >= len(tokens) or tokens[i]["value"] != "(":
        _error("Expected '(' after VALUES.", tokens[i] if i < len(tokens) else None)

    if tokens[-1]["value"] != ")":
        _error("Expected ')' at the end of VALUES.", tokens[-1])

    _check_parentheses(tokens[i:])

    values = _split_top_level(tokens[i + 1:-1])

    return {
        "type": "InsertStatement",
        "table": table_name,
        "columns": columns,
        "values": [[t["value"] for t in part] for part in values]
    }


def parse_sql(sql_or_tokens):
    """
    Parse SQL text or an existing lexer token list.

    Returns an AST dictionary.
    Raises SQLSyntaxError when the structure is invalid.
    """
    tokens = tokenize(sql_or_tokens) if isinstance(sql_or_tokens, str) else list(sql_or_tokens)

    if not tokens:
        _error("Enter a SQL statement.")

    tokens = _remove_final_semicolon(tokens)

    if not tokens:
        _error("Enter a SQL statement.")

    _check_parentheses(tokens)

    first = tokens[0]["value"].upper()

    if first == "SELECT":
        return _parse_select(tokens)

    if first == "CREATE":
        return _parse_create(tokens)

    if first == "INSERT":
        return _parse_insert(tokens)

    _error(
        "Supported statements are SELECT, CREATE TABLE, and INSERT INTO.",
        tokens[0]
    )
