import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent / "modules"))

from compiler import compile_sql
schema = {
    "students": [
        {"name": "student_id"},
        {"name": "name"},
        {"name": "age"},
        {"name": "department"},
        {"name": "marks"},
    ],
    "courses": [
        {"name": "course_id"},
        {"name": "course_name"},
    ],
}

queries = [
    "SELECT name, marks FROM students WHERE marks >= 90;",
    "SELECT student_name FROM students;",
    "SELECT name FROM unknown_table;",
    "SELECT * FROM students;",
    "SELECT name students;",
]


for sql in queries:
    print("\n" + "=" * 50)
    print("SQL:", sql)

    result = compile_sql(sql, schema)

    print("\nTokens:")
    for token in result["tokens"]:
        print(token)

    print("\nAST:")
    print(result["ast"])

    print("\nSuccess:", result["success"])

    print("\nDiagnostics:")
    if result["diagnostics"]:
        for diagnostic in result["diagnostics"]:
            print(
                diagnostic["stage"],
                "-",
                diagnostic["message"],
                f"(Line {diagnostic['line']}, "
                f"Column {diagnostic['column']})"
            )
    else:
        print("No errors found.")