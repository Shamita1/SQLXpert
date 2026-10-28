"""
Defines the 5 chapters, challenges, test cases, and difficulty parameters.
"""

CHAPTERS = [
    {
        "id": 1,
        "title": "SQL Foundations",
        "description": "Master basic filtering, sorting, and aggregate functions.",
        "badge_req": "Junior DBA",
        "challenges": [
            {
                "id": "ch1_q1",
                "title": "High-Value Customer Filter",
                "difficulty": "Normal",
                "time_limit": 300, # 5 mins
                "base_xp": 100,
                "base_coins": 20,
                "prompt": "Write a SQL query to retrieve customer names and total spending from the `orders` table where total spending exceeds 500, ordered by spending descending.",
                "schema_hint": "Tables: customers(id, name), orders(order_id, customer_id, amount)",
                "test_cases": [
                    {"input": {}, "expected": [{"name": "Alice", "total": 650}, {"name": "Bob", "total": 520}]}
                ]
            },
            {
                "id": "ch1_q2",
                "title": "Departmental Headcount Grouping",
                "difficulty": "Normal",
                "time_limit": 300,
                "base_xp": 120,
                "base_coins": 25,
                "prompt": "Find the department name and employee count for departments having more than 5 employees using GROUP BY and HAVING.",
                "schema_hint": "Tables: departments(dept_id, dept_name), employees(emp_id, dept_id, name)",
                "test_cases": []
            }
        ]
    },
    {
        "id": 2,
        "title": "Relational Mastery",
        "description": "Handle multi-table joins, subqueries, and Common Table Expressions (CTEs).",
        "badge_req": "Query Optimizer",
        "challenges": [
            {
                "id": "ch2_q1",
                "title": "Recursive Org Hierarchy CTE",
                "difficulty": "Intermediate",
                "time_limit": 600, # 10 mins
                "base_xp": 250,
                "base_coins": 50,
                "prompt": "Use a recursive CTE to find all reporting employee chains under Manager ID 1.",
                "schema_hint": "Tables: staff(emp_id, name, manager_id)",
                "test_cases": []
            }
        ]
    },
    {
        "id": 3,
        "title": "Advanced Analytical SQL",
        "description": "Leverage window functions, running totals, and ranking.",
        "badge_req": "Data Architect",
        "challenges": [
            {
                "id": "ch3_q1",
                "title": "Running Total with Window Functions",
                "difficulty": "Expert",
                "time_limit": 900, # 15 mins
                "base_xp": 400,
                "base_coins": 80,
                "prompt": "Calculate a running total of sales partitioned by region ordered by transaction date using SUM() OVER().",
                "schema_hint": "Tables: transactions(txn_id, region, amount, txn_date)",
                "test_cases": []
            }
        ]
    },
    {
        "id": 4,
        "title": "PL/SQL Procedural Basics",
        "description": "Anonymous blocks, variables (%TYPE, %ROWTYPE), and control structures.",
        "badge_req": "Procedural Scripter",
        "challenges": [
            {
                "id": "ch4_q1",
                "title": "Conditional Bonus Calculator Block",
                "difficulty": "Hard",
                "time_limit": 900,
                "base_xp": 500,
                "base_coins": 100,
                "prompt": "Write an anonymous PL/SQL block using IF-THEN-ELSE to calculate employee bonus percentages based on performance rating.",
                "schema_hint": "Use DECLARE, BEGIN, DBMS_OUTPUT.PUT_LINE",
                "is_plsql": True,
                "test_cases": []
            }
        ]
    },
    {
        "id": 5,
        "title": "PL/SQL Enterprise Logic",
        "description": "Stored procedures, explicit cursors, and database triggers.",
        "badge_req": "PL/SQL Grandmaster",
        "challenges": [
            {
                "id": "ch5_q1",
                "title": "Audit Trail Trigger Implementation",
                "difficulty": "Master",
                "time_limit": 1200, # 20 mins
                "base_xp": 800,
                "base_coins": 150,
                "prompt": "Create a BEFORE UPDATE trigger on the inventory table that logs old and new stock levels into an audit table.",
                "schema_hint": "Use CREATE OR REPLACE TRIGGER ... FOR EACH ROW",
                "is_plsql": True,
                "test_cases": []
            }
        ]
    }
]