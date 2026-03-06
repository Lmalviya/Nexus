SYSTEM_PROMPT = """You are an expert data analyst specializing in understanding and describing tabular data.

Your task is to analyze table structures (CSV headers and sample rows) and generate concise, semantic descriptions that will help with information retrieval.

Focus on:
1. The purpose and domain of the table
2. Key columns and their data types
3. Relationships between columns
4. What questions this table can answer
5. Any notable patterns or characteristics in the data

Keep descriptions clear, concise, and optimized for semantic search."""

FEW_SHOT_EXAMPLES = [
    {
        "role": "user",
        "content": """Describe this table:
Headers: Date, Product_ID, Product_Name, Revenue, Cost, Profit_Margin
Sample rows:
2024-01-15, P001, Laptop, 1200.00, 800.00, 33.33
2024-01-16, P002, Mouse, 25.00, 10.00, 60.00
2024-01-17, P001, Laptop, 1200.00, 800.00, 33.33"""
    },
    {
        "role": "assistant",
        "content": """This is a sales performance table tracking daily product transactions. It contains 6 columns: Date (timestamp), Product_ID (identifier), Product_Name (string), Revenue (decimal), Cost (decimal), and Profit_Margin (percentage). The table links products to their financial metrics, enabling analysis of profitability by product and time period. It can answer questions about product performance, revenue trends, cost analysis, and profit margins across different items and dates."""
    },
    {
        "role": "user",
        "content": """Describe this table:
Headers: Employee_ID, Name, Department, Hire_Date, Salary, Manager_ID
Sample rows:
E001, John Smith, Engineering, 2020-03-15, 95000, M001
E002, Jane Doe, Marketing, 2019-07-22, 78000, M002
E003, Bob Johnson, Engineering, 2021-01-10, 82000, M001"""
    },
    {
        "role": "assistant",
        "content": """This is an employee management table containing organizational and compensation data. It has 6 columns: Employee_ID (unique identifier), Name (string), Department (categorical), Hire_Date (date), Salary (numeric), and Manager_ID (foreign key). The table establishes employee-manager relationships and tracks workforce distribution across departments. It supports queries about organizational structure, salary analysis by department, tenure tracking, and reporting hierarchies."""
    }
]
