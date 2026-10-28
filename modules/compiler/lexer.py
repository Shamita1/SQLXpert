
import re

# SQL words recognized by the lexer.
KEYWORDS = set("""
    SELECT FROM WHERE AND OR NOT NULL IS IN LIKE BETWEEN
    AS DISTINCT ORDER BY ASC DESC LIMIT OFFSET
    JOIN INNER LEFT RIGHT FULL OUTER CROSS ON USING
    GROUP HAVING COUNT SUM AVG MIN MAX
    INSERT INTO VALUES DEFAULT
    CREATE TABLE IF EXISTS
    UPDATE SET DELETE DROP ALTER
    UNION ALL CASE WHEN THEN ELSE END
    EXISTS PRIMARY KEY FOREIGN REFERENCES
    UNIQUE CHECK CONSTRAINT
    INTEGER INT REAL FLOAT DOUBLE TEXT VARCHAR CHAR
    BLOB NUMERIC DECIMAL BOOLEAN DATE DATETIME
""".split())

# Token patterns are tested from left to right.
TOKEN_RE = re.compile(
    r"(?P<WHITESPACE>\s+)"
    r"|(?P<COMMENT>--[^\n]*|/\*[\s\S]*?\*/)"
    r"|(?P<UNTERMINATED_COMMENT>/\*[\s\S]*)"
    r"|(?P<STRING>'(?:''|[^'])*')"
    r"|(?P<UNTERMINATED_STRING>'(?:''|[^'])*$)"
    r'|(?P<QUOTED_IDENTIFIER>"(?:""|[^"])*"|`[^`]*`|\[[^\]]*\])'
    r"|(?P<NUMBER>\d+(?:\.\d+)?(?:[eE][+-]?\d+)?)"
    r"|(?P<OPERATOR><=|>=|<>|!=|==|=|<|>|\|\||[+\-*/%])"
    r"|(?P<PUNCTUATION>[(),.;])"
    r"|(?P<IDENTIFIER>[A-Za-z_][A-Za-z0-9_$]*)"
    r"|(?P<UNKNOWN>.)"
)


def tokenize(sql):
    """
    Convert SQL text into tokens.

    Each token contains:
        type   : token category
        value  : original SQL text
        line   : 1-based line number
        column : 1-based column number

    Raises ValueError for unterminated comments or strings.
    """
    if not isinstance(sql, str):
        raise TypeError("SQL input must be a string.")

    tokens = []
    line = 1
    column = 1
    position = 0

    while position < len(sql):
        match = TOKEN_RE.match(sql, position)

        if not match:
            raise ValueError(
                f"Unable to tokenize SQL at line {line}, column {column}."
            )

        kind = match.lastgroup
        value = match.group()
        token_line = line
        token_column = column

        # Calculate the position of the next token.
        newlines = value.count("\n")

        if newlines:
            line += newlines
            column = len(value.rsplit("\n", 1)[-1]) + 1
        else:
            column += len(value)

        position = match.end()

        # Ignore whitespace and comments.
        if kind in ("WHITESPACE", "COMMENT"):
            continue

        if kind == "UNTERMINATED_COMMENT":
            raise ValueError(
                f"Unterminated block comment at line "
                f"{token_line}, column {token_column}."
            )

        if kind == "UNTERMINATED_STRING":
            raise ValueError(
                f"Unterminated string literal at line "
                f"{token_line}, column {token_column}."
            )

        if kind == "IDENTIFIER":
            if value.upper() in KEYWORDS:
                kind = "KEYWORD"

        elif kind == "QUOTED_IDENTIFIER":
            kind = "IDENTIFIER"

        elif kind == "UNKNOWN":
            raise ValueError(
                f"Unexpected character {value!r} at line "
                f"{token_line}, column {token_column}."
            )

        tokens.append({
            "type": kind,
            "value": value,
            "line": token_line,
            "column": token_column
        })

    return tokens
