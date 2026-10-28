
_SETUP_SQL = """
CREATE TABLE students (
    student_id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    age INTEGER,
    department TEXT,
    marks INTEGER
);

INSERT INTO students VALUES
    (1, 'Anu', 20, 'CSE', 85),
    (2, 'Ben', 19, 'ECE', 72),
    (3, 'Cara', 21, 'CSE', 91),
    (4, 'David', 18, 'IT', 65),
    (5, 'Eva', 22, 'ECE', 88),
    (6, 'Farah', 20, 'CSE', 95);

CREATE TABLE courses (
    course_id INTEGER PRIMARY KEY,
    course_name TEXT NOT NULL
);

INSERT INTO courses VALUES
    (101, 'Database Systems'),
    (102, 'Compiler Design'),
    (103, 'Operating Systems'),
    (104, 'Computer Networks');

CREATE TABLE enrollments (
    student_id INTEGER,
    course_id INTEGER
);

INSERT INTO enrollments VALUES
    (1, 101), (1, 102),
    (2, 101), (2, 104),
    (3, 102), (3, 103),
    (4, 103),
    (5, 101), (5, 104),
    (6, 101), (6, 102), (6, 103);

CREATE TABLE employees (
    employee_id INTEGER PRIMARY KEY,
    name TEXT,
    department TEXT,
    salary INTEGER
);

INSERT INTO employees VALUES
    (1, 'John', 'IT', 60000),
    (2, 'Priya', 'HR', 45000),
    (3, 'Sam', 'IT', 75000),
    (4, 'Maya', 'Finance', 55000),
    (5, 'Arun', 'HR', 50000),
    (6, 'Leah', 'Finance', 80000);
"""

CHALLENGES = [
    # ==================== EASY: 1–8 ====================
    {
        "id": 1,
        "title": "Display Student Details",
        "difficulty": "Easy",
        "topic": "SELECT",
        "description": "Display the name and department of every student.",
        "schema": "students(student_id, name, age, department, marks)",
        "hint": "Select the two required columns from the students table.",
        "setup_sql": _SETUP_SQL,
        "solution_sql": """
            SELECT name, department
            FROM students
            ORDER BY student_id;
        """,
        "points": 10,
    },
    {
        "id": 2,
        "title": "Students Scoring Above 80",
        "difficulty": "Easy",
        "topic": "WHERE",
        "description": "Find the names of students who scored more than 80 marks.",
        "schema": "students(student_id, name, age, department, marks)",
        "hint": "Use WHERE to filter marks greater than 80.",
        "setup_sql": _SETUP_SQL,
        "solution_sql": """
            SELECT name FROM students
            WHERE marks > 80
            ORDER BY student_id;
        """,
        "points": 10,
    },
    {
        "id": 3,
        "title": "Find CSE Students",
        "difficulty": "Easy",
        "topic": "WHERE",
        "description": "Display all details of students belonging to CSE.",
        "schema": "students(student_id, name, age, department, marks)",
        "hint": "Filter the department column using the value CSE.",
        "setup_sql": _SETUP_SQL,
        "solution_sql": """
            SELECT * FROM students
            WHERE department = 'CSE'
            ORDER BY student_id;
        """,
        "points": 10,
    },
    {
        "id": 4,
        "title": "Sort by Marks",
        "difficulty": "Easy",
        "topic": "ORDER BY",
        "description": "Display student names and marks from highest to lowest.",
        "schema": "students(student_id, name, age, department, marks)",
        "hint": "Use ORDER BY marks with descending order.",
        "setup_sql": _SETUP_SQL,
        "solution_sql": """
            SELECT name, marks FROM students
            ORDER BY marks DESC;
        """,
        "points": 10,
    },
    {
        "id": 5,
        "title": "Count All Students",
        "difficulty": "Easy",
        "topic": "COUNT",
        "description": "Find the total number of students. Name the result total_students.",
        "schema": "students(student_id, name, age, department, marks)",
        "hint": "Use COUNT(*) with the alias total_students.",
        "setup_sql": _SETUP_SQL,
        "solution_sql": """
            SELECT COUNT(*) AS total_students FROM students;
        """,
        "points": 10,
    },
    {
        "id": 6,
        "title": "Alphabetical Student List",
        "difficulty": "Easy",
        "topic": "ORDER BY",
        "description": "Display all student names in alphabetical order.",
        "schema": "students(student_id, name, age, department, marks)",
        "hint": "Sort the name column in ascending order.",
        "setup_sql": _SETUP_SQL,
        "solution_sql": """
            SELECT name FROM students ORDER BY name ASC;
        """,
        "points": 10,
    },
    {
        "id": 7,
        "title": "Students Scoring at Least 90",
        "difficulty": "Easy",
        "topic": "WHERE",
        "description": "Display student names and marks for marks greater than or equal to 90.",
        "schema": "students(student_id, name, age, department, marks)",
        "hint": "Use the >= comparison operator.",
        "setup_sql": _SETUP_SQL,
        "solution_sql": """
            SELECT name, marks FROM students
            WHERE marks >= 90
            ORDER BY student_id;
        """,
        "points": 10,
    },
    {
        "id": 8,
        "title": "Unique Departments",
        "difficulty": "Easy",
        "topic": "DISTINCT",
        "description": "List each department only once, in alphabetical order.",
        "schema": "students(student_id, name, age, department, marks)",
        "hint": "Use DISTINCT to remove duplicate department names.",
        "setup_sql": _SETUP_SQL,
        "solution_sql": """
            SELECT DISTINCT department FROM students
            ORDER BY department;
        """,
        "points": 10,
    },

    # ================= MEDIUM: 9–16 =================
    {
        "id": 9,
        "title": "Count Students by Department",
        "difficulty": "Medium",
        "topic": "GROUP BY",
        "description": "Display each department and its student count. Name the count student_count.",
        "schema": "students(student_id, name, age, department, marks)",
        "hint": "Group by department and count the rows in each group.",
        "setup_sql": _SETUP_SQL,
        "solution_sql": """
            SELECT department, COUNT(*) AS student_count
            FROM students
            GROUP BY department
            ORDER BY department;
        """,
        "points": 20,
    },
    {
        "id": 10,
        "title": "Average Marks",
        "difficulty": "Medium",
        "topic": "AVG",
        "description": "Find the average marks of all students. Name the result average_marks.",
        "schema": "students(student_id, name, age, department, marks)",
        "hint": "Use AVG() on the marks column.",
        "setup_sql": _SETUP_SQL,
        "solution_sql": """
            SELECT AVG(marks) AS average_marks FROM students;
        """,
        "points": 20,
    },
    {
        "id": 11,
        "title": "Top-Scoring Student",
        "difficulty": "Medium",
        "topic": "ORDER BY LIMIT",
        "description": "Find the name and marks of the highest-scoring student.",
        "schema": "students(student_id, name, age, department, marks)",
        "hint": "Sort marks in descending order and return only one row.",
        "setup_sql": _SETUP_SQL,
        "solution_sql": """
            SELECT name, marks FROM students
            ORDER BY marks DESC LIMIT 1;
        """,
        "points": 20,
    },
    {
        "id": 12,
        "title": "Students and Their Courses",
        "difficulty": "Medium",
        "topic": "JOIN",
        "description": "Display each student's name and the course they are enrolled in.",
        "schema": "students, enrollments, courses",
        "hint": "Join students to enrollments using student_id, then join courses using course_id.",
        "setup_sql": _SETUP_SQL,
        "solution_sql": """
            SELECT s.name, c.course_name
            FROM students s
            JOIN enrollments e ON s.student_id = e.student_id
            JOIN courses c ON e.course_id = c.course_id
            ORDER BY s.name, c.course_name;
        """,
        "points": 20,
    },
    {
        "id": 13,
        "title": "Number of Enrollments per Course",
        "difficulty": "Medium",
        "topic": "JOIN GROUP BY",
        "description": "Display every course and its enrollment count, including courses with zero enrollments. Name the count enrollment_count.",
        "schema": "courses(course_id, course_name), enrollments(student_id, course_id)",
        "hint": "Use LEFT JOIN and GROUP BY so courses without enrollments remain in the results.",
        "setup_sql": _SETUP_SQL,
        "solution_sql": """
            SELECT c.course_name, COUNT(e.student_id) AS enrollment_count
            FROM courses c
            LEFT JOIN enrollments e ON c.course_id = e.course_id
            GROUP BY c.course_id, c.course_name
            ORDER BY c.course_name;
        """,
        "points": 20,
    },
    {
        "id": 14,
        "title": "Older High-Scoring Students",
        "difficulty": "Medium",
        "topic": "WHERE AND",
        "description": "Find the names of students aged at least 20 who scored above 80.",
        "schema": "students(student_id, name, age, department, marks)",
        "hint": "Combine both conditions using AND.",
        "setup_sql": _SETUP_SQL,
        "solution_sql": """
            SELECT name FROM students
            WHERE age >= 20 AND marks > 80
            ORDER BY student_id;
        """,
        "points": 20,
    },
    {
        "id": 15,
        "title": "Departments with High Average Marks",
        "difficulty": "Medium",
        "topic": "GROUP BY HAVING",
        "description": "Show departments whose average marks are greater than 80. Display department and average_marks.",
        "schema": "students(student_id, name, age, department, marks)",
        "hint": "Use GROUP BY department and HAVING AVG(marks) > 80.",
        "setup_sql": _SETUP_SQL,
        "solution_sql": """
            SELECT department, AVG(marks) AS average_marks
            FROM students
            GROUP BY department
            HAVING AVG(marks) > 80
            ORDER BY department;
        """,
        "points": 20,
    },
    {
        "id": 16,
        "title": "Employees Earning Above 60000",
        "difficulty": "Medium",
        "topic": "WHERE ORDER BY",
        "description": "Display employee names, departments, and salaries for employees earning more than 60000, sorted by salary from highest to lowest.",
        "schema": "employees(employee_id, name, department, salary)",
        "hint": "Filter salary first, then sort the matching rows in descending order.",
        "setup_sql": _SETUP_SQL,
        "solution_sql": """
            SELECT name, department, salary
            FROM employees
            WHERE salary > 60000
            ORDER BY salary DESC;
        """,
        "points": 20,
    },

    # ================== HARD: 17–24 ==================
    {
        "id": 17,
        "title": "Above-Average Students",
        "difficulty": "Hard",
        "topic": "SUBQUERY",
        "description": "Find students whose marks are greater than the average marks of all students. Display name and marks.",
        "schema": "students(student_id, name, age, department, marks)",
        "hint": "Use a subquery that calculates AVG(marks).",
        "setup_sql": _SETUP_SQL,
        "solution_sql": """
            SELECT name, marks FROM students
            WHERE marks > (SELECT AVG(marks) FROM students)
            ORDER BY student_id;
        """,
        "points": 30,
    },
    {
        "id": 18,
        "title": "Department Toppers",
        "difficulty": "Hard",
        "topic": "CORRELATED SUBQUERY",
        "description": "Find the student or students with the highest marks in each department. Display name, department, and marks.",
        "schema": "students(student_id, name, age, department, marks)",
        "hint": "Compare each student's marks with the maximum marks for that student's department.",
        "setup_sql": _SETUP_SQL,
        "solution_sql": """
            SELECT s.name, s.department, s.marks
            FROM students s
            WHERE s.marks = (
                SELECT MAX(s2.marks)
                FROM students s2
                WHERE s2.department = s.department
            )
            ORDER BY s.department, s.name;
        """,
        "points": 30,
    },
    {
        "id": 19,
        "title": "Departments Above a Student Count",
        "difficulty": "Hard",
        "topic": "GROUP BY HAVING",
        "description": "Find departments containing at least two students. Display department and student_count.",
        "schema": "students(student_id, name, age, department, marks)",
        "hint": "Group by department and filter groups using HAVING COUNT(*).",
        "setup_sql": _SETUP_SQL,
        "solution_sql": """
            SELECT department, COUNT(*) AS student_count
            FROM students
            GROUP BY department
            HAVING COUNT(*) >= 2
            ORDER BY department;
        """,
        "points": 30,
    },
    {
        "id": 20,
        "title": "Students Taking Database Systems",
        "difficulty": "Hard",
        "topic": "JOIN WHERE",
        "description": "Find the names of students enrolled in Database Systems. Display each name once, alphabetically.",
        "schema": "students, enrollments, courses",
        "hint": "Join all three tables and filter by the course name. DISTINCT prevents duplicate names.",
        "setup_sql": _SETUP_SQL,
        "solution_sql": """
            SELECT DISTINCT s.name
            FROM students s
            JOIN enrollments e ON s.student_id = e.student_id
            JOIN courses c ON e.course_id = c.course_id
            WHERE c.course_name = 'Database Systems'
            ORDER BY s.name;
        """,
        "points": 30,
    },
    {
        "id": 21,
        "title": "Employee Salary Categories",
        "difficulty": "Hard",
        "topic": "CASE",
        "description": "Display each employee's name and salary category. Categorize salaries of 70000 or more as High, salaries of 50000 or more as Medium, and the rest as Low. Name the category column salary_category.",
        "schema": "employees(employee_id, name, department, salary)",
        "hint": "Use CASE WHEN conditions in descending salary thresholds.",
        "setup_sql": _SETUP_SQL,
        "solution_sql": """
            SELECT name,
                   CASE
                       WHEN salary >= 70000 THEN 'High'
                       WHEN salary >= 50000 THEN 'Medium'
                       ELSE 'Low'
                   END AS salary_category
            FROM employees
            ORDER BY employee_id;
        """,
        "points": 30,
    },
    {
        "id": 22,
        "title": "Students Enrolled in Multiple Courses",
        "difficulty": "Hard",
        "topic": "JOIN GROUP BY HAVING",
        "description": "Find students enrolled in at least two courses. Display student name and course_count.",
        "schema": "students(student_id, name, age, department, marks), enrollments(student_id, course_id)",
        "hint": "Join students with enrollments, group by student, and filter using HAVING COUNT(*).",
        "setup_sql": _SETUP_SQL,
        "solution_sql": """
            SELECT s.name, COUNT(e.course_id) AS course_count
            FROM students s
            JOIN enrollments e ON s.student_id = e.student_id
            GROUP BY s.student_id, s.name
            HAVING COUNT(e.course_id) >= 2
            ORDER BY s.name;
        """,
        "points": 30,
    },
    {
        "id": 23,
        "title": "Compare Department and Overall Averages",
        "difficulty": "Hard",
        "topic": "SUBQUERY GROUP BY",
        "description": "Display each department's average marks only when that average is greater than the overall student average. Name the average column department_average.",
        "schema": "students(student_id, name, age, department, marks)",
        "hint": "Use GROUP BY department and compare AVG(marks) against a subquery for the overall average.",
        "setup_sql": _SETUP_SQL,
        "solution_sql": """
            SELECT department, AVG(marks) AS department_average
            FROM students
            GROUP BY department
            HAVING AVG(marks) > (SELECT AVG(marks) FROM students)
            ORDER BY department;
        """,
        "points": 30,
    },
    {
        "id": 24,
        "title": "Students Taking Every Course",
        "difficulty": "Hard",
        "topic": "GROUP BY HAVING SUBQUERY",
        "description": "Find students enrolled in every course listed in the courses table. Display their names alphabetically.",
        "schema": "students, enrollments, courses",
        "hint": "Compare each student's distinct course count with the total number of courses.",
        "setup_sql": _SETUP_SQL,
        "solution_sql": """
            SELECT s.name
            FROM students s
            JOIN enrollments e ON s.student_id = e.student_id
            GROUP BY s.student_id, s.name
            HAVING COUNT(DISTINCT e.course_id) = (
                SELECT COUNT(*) FROM courses
            )
            ORDER BY s.name;
        """,
        "points": 30,
    },
]
