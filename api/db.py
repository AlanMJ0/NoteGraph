import os
import psycopg
from psycopg import sql
from typing import LiteralString, cast
from dotenv import load_dotenv

load_dotenv()
DATABASE_URL=os.getenv("DATABASE_URL")

def get_connection():
    if not DATABASE_URL:
        raise ValueError("DATABASE_URL is not set in your .env file")
    return psycopg.connect(DATABASE_URL)

def init_db(schema_path: str="sql/schema.sql"):
    if not os.path.exists(schema_path):
        print(f"Error: Could not find the schema file at {schema_path}")
        return

    with open(schema_path, "r", encoding="utf-8") as f:
        schema_sql=cast(LiteralString,f.read())

    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(sql.SQL(schema_sql))
        conn.commit()
    print("PostgreSQL tables successfully initialized")


if __name__=="__main__":
    print("Initializing database tables..")
    init_db()





