import psycopg2
import os
from dotenv import load_dotenv

load_dotenv()

def get_db_connection():
    conn = psycopg2.connect(
        os.getenv("DATABASE_URL"),
        sslmode="require"   # 👈 Add this line
    )
    return conn