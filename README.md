# SQLXpert — SQL Learning, Debugging and Compiler Trace

A beginner-friendly Compiler Design Lab prototype built with Flask, SQLite, HTML, CSS and JavaScript.

## Features included

- SQL workspace with example queries and tabular output
- Educational lexical tokenizer with token types and source locations
- Lightweight SELECT structure checks and a simplified AST
- Schema browser for the demo tables
- Read-only query execution guard and basic query timeout
- SQLite query plan using `EXPLAIN QUERY PLAN`
- Error diagnosis using parser/database evidence
- Rule-based English-to-SQL demo (no LLM or API key required)
- SQL clause explanation
- Three SQL challenges with output comparison
- Persistent query history and learning statistics
- TraceLearn panel linking evidence, findings and next steps

## Important scope note

This is a working educational prototype, not a full SQL compiler. The lexer and parser support a limited, documented subset and do not replace SQLite's own SQL parser. The English-to-SQL generator is rule-based and must not be described as a real LLM. Query plans are SQLite plans, not PostgreSQL plans.

## Requirements

- Python 3.10 or newer
- VS Code (recommended)
- Internet is not required for backend functionality. Google Fonts are optional styling.

## Run on Windows

1. Extract the ZIP to a folder such as `C:\SQLXpert`.
2. Open VS Code.
3. Choose **File → Open Folder** and select the extracted `SQLXpert` folder.
4. Choose **Terminal → New Terminal**.
5. Create a virtual environment:

   ```powershell
   py -m venv .venv
   ```

6. Activate it in PowerShell:

   ```powershell
   .\.venv\Scripts\Activate.ps1
   ```

   If PowerShell blocks activation, use Command Prompt terminal and run:

   ```bat
   .venv\Scripts\activate.bat
   ```

7. Install dependencies:

   ```powershell
   python -m pip install -r requirements.txt
   ```

8. Start the app:

   ```powershell
   python app.py
   ```

9. Open `http://127.0.0.1:5000` in Chrome or Edge.

The `sqlxpert.db` SQLite database is created automatically on first launch and seeded with sample data. Keep the terminal open while using the app. Press `Ctrl+C` in the terminal to stop the server.

## Suggested demo sequence

1. Run `SELECT name, department, marks FROM students WHERE marks >= 85 ORDER BY marks DESC;`
2. Open Compiler Trace and inspect the tokens and AST.
3. Try `SELECT nam FROM students;` and use Diagnose query to see the database's missing-column evidence.
4. Click Explain plan on a valid query.
5. Open SQL Challenges and submit a solution.
6. Open Query History to show saved attempts.
7. Click Generate from English and explain honestly that the starter uses an offline rule-based generator.

## Security limitations

The demo blocks obvious non-SELECT statements and stores data locally. This is not a hardened public deployment. Do not expose the development server to the internet or use real confidential data. A production version needs stronger SQL parsing/authorization, isolation, authentication, rate limiting and deployment hardening.

## Suggested next enhancements

- Replace the lightweight parser with a maintained SQL parser and document the grammar/dialect.
- Add a real LLM provider behind a server-side environment variable and validate every generated query.
- Add unit tests for tokens, malformed SQL, column errors, challenges and SQL safety.
- Add before/after AST diff and link plan nodes to logical operations only when mappings are reliable.

## Create your own tables (added feature)

SQLXpert supports custom tables in two ways:

1. In the **Create and manage your own data** panel, enter a table name and columns such as `id INTEGER, name TEXT, salary REAL`, then choose **Create table**.
2. Add a row through the form by choosing the table and entering JSON column values, for example `{"id": 1, "name": "Priya", "salary": 50000}`.
3. Or use the SQL editor:

```sql
CREATE TABLE employees (
  id INTEGER,
  name TEXT,
  salary REAL
);

INSERT INTO employees (id, name, salary)
VALUES (1, 'Priya', 50000);

SELECT name, salary
FROM employees
WHERE salary > 30000;
```

Run each statement separately. Supported commands in the editor are `SELECT`, `CREATE TABLE`, and `INSERT INTO ... VALUES`. This learning demo blocks `UPDATE`, `DELETE`, `DROP`, and other commands. The database is a local SQLite file named `sqlxpert.db` in the project folder.
