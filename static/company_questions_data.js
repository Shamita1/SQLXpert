
const companyQuestions = [
    {
        id: 1,
        title: "High-Earning Employees",
        company: "Amazon",
        difficulty: "Easy",
        topic: "Filtering",
        description: "Find employees whose salary is greater than 60000.",
        schema: "employees(employee_id, name, department, salary)",
        solution: "SELECT name, salary FROM employees WHERE salary > 60000;"
    },
    {
        id: 2,
        title: "Average Salary by Department",
        company: "Amazon",
        difficulty: "Medium",
        topic: "GROUP BY",
        description: "Calculate the average salary for each department.",
        schema: "employees(employee_id, name, department, salary)",
        solution: "SELECT department, AVG(salary) AS average_salary FROM employees GROUP BY department;"
    },
    {
        id: 3,
        title: "Second-Highest Salary",
        company: "Microsoft",
        difficulty: "Medium",
        topic: "Subqueries",
        description: "Find the second-highest distinct salary.",
        schema: "employees(employee_id, name, department, salary)",
        solution: "SELECT MAX(salary) AS second_highest_salary FROM employees WHERE salary < (SELECT MAX(salary) FROM employees);"
    },
    {
        id: 4,
        title: "Employees Without a Department",
        company: "Microsoft",
        difficulty: "Easy",
        topic: "NULL",
        description: "Find employees who do not have a department assigned.",
        schema: "employees(employee_id, name, department, salary)",
        solution: "SELECT name FROM employees WHERE department IS NULL;"
    },
    {
        id: 5,
        title: "Customers With No Orders",
        company: "Google",
        difficulty: "Medium",
        topic: "JOIN",
        description: "Find customers who have never placed an order.",
        schema: "customers(customer_id, customer_name); orders(order_id, customer_id, amount)",
        solution: "SELECT c.customer_id, c.customer_name FROM customers c LEFT JOIN orders o ON c.customer_id = o.customer_id WHERE o.order_id IS NULL;"
    },
    {
        id: 6,
        title: "Count Orders per Customer",
        company: "Google",
        difficulty: "Easy",
        topic: "Aggregate Functions",
        description: "Count the number of orders placed by each customer.",
        schema: "orders(order_id, customer_id, order_date, amount)",
        solution: "SELECT customer_id, COUNT(*) AS order_count FROM orders GROUP BY customer_id;"
    },
    {
        id: 7,
        title: "Employees Above Department Average",
        company: "Accenture",
        difficulty: "Hard",
        topic: "Subqueries",
        description: "Find employees who earn more than their department's average salary.",
        schema: "employees(employee_id, name, department, salary)",
        solution: "SELECT e.name, e.department, e.salary FROM employees e WHERE e.salary > (SELECT AVG(e2.salary) FROM employees e2 WHERE e2.department = e.department);"
    },
    {
        id: 8,
        title: "Highest and Lowest Salary",
        company: "Accenture",
        difficulty: "Medium",
        topic: "Aggregate Functions",
        description: "Display the highest and lowest salary for each department.",
        schema: "employees(employee_id, name, department, salary)",
        solution: "SELECT department, MAX(salary) AS highest_salary, MIN(salary) AS lowest_salary FROM employees GROUP BY department;"
    },
    {
        id: 9,
        title: "Employees in Alphabetical Order",
        company: "TCS",
        difficulty: "Easy",
        topic: "ORDER BY",
        description: "Display employee names in alphabetical order.",
        schema: "employees(employee_id, name, department, salary)",
        solution: "SELECT name FROM employees ORDER BY name ASC;"
    },
    {
        id: 10,
        title: "Departments With More Than Five Employees",
        company: "TCS",
        difficulty: "Medium",
        topic: "HAVING",
        description: "Find departments with more than five employees.",
        schema: "employees(employee_id, name, department, salary)",
        solution: "SELECT department, COUNT(*) AS employee_count FROM employees GROUP BY department HAVING COUNT(*) > 5;"
    }
];
