from .lexer import tokenize
from .parser import parse_sql, SQLSyntaxError
from .analyzer import analyze


def analyze_sql(sql, schema=None):
    result = analyze(sql, schema)

    return (
        result["tokens"],
        result["ast"],
        result["diagnostics"]
    )


def compile_sql(sql, schema=None):
    return analyze(sql, schema)


__all__ = [
    "tokenize",
    "parse_sql",
    "SQLSyntaxError",
    "analyze",
    "analyze_sql",
    "compile_sql",
]