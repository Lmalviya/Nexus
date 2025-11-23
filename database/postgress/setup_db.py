import os
import psycopg2
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

DB_HOST = os.getenv("DB_HOST")
DB_PORT = os.getenv("DB_PORT")
DB_NAME = os.getenv("DB_NAME")
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")

def setup_database():
    try:
        # Connect to the database
        conn = psycopg2.connect(
            host=DB_HOST,
            port=DB_PORT,
            dbname=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD
        )
        conn.autocommit = True
        cursor = conn.cursor()

        # Read schema.sql
        with open("schema.sql", "r") as f:
            schema_sql = f.read()

        # Execute schema
        print("Executing schema...")
        cursor.execute(schema_sql)
        print("Schema executed successfully.")

        cursor.close()
        conn.close()

    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    setup_database()
