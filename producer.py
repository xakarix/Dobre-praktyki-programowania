import sqlite3
import uuid
import sys

DB_NAME = "tasks.db"

def initialize_db():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS tasks (
            id TEXT PRIMARY KEY,
            status TEXT
        )
    """)
    conn.commit()
    conn.close()

def add_tasks(count=100):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    for _ in range(count):
        task_id = str(uuid.uuid4())
        cursor.execute(
            "INSERT INTO tasks (id, status) VALUES (?, ?)",
            (task_id, "pending")
        )
    
    conn.commit()
    conn.close()
    print(f"Producent: Dodano {count} zadań do bazy.")

if __name__ == "__main__":
    initialize_db()
    num_tasks = int(sys.argv[1]) if len(sys.argv) > 1 else 100
    add_tasks(num_tasks)