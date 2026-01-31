import sqlite3
import time

DB_NAME = "tasks.db"

def claim_task():
    """Atomowo pobiera zadanie 'pending' i zmienia jego status na 'in_progress'."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    cursor.execute("BEGIN TRANSACTION")
    
    cursor.execute("SELECT id FROM tasks WHERE status = 'pending' LIMIT 1")
    row = cursor.fetchone()
    
    if row:
        task_id = row[0]
        cursor.execute("UPDATE tasks SET status = 'in_progress' WHERE id = ?", (task_id,))
        conn.commit()
        conn.close()
        return task_id
    
    conn.rollback()
    conn.close()
    return None

def update_status(task_id, status):
    """Aktualizuje status zadania (np. na 'done')."""
    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()
        cursor.execute("UPDATE tasks SET status = ? WHERE id = ?", (status, task_id))
        conn.commit()

def consume():
    print("Konsument uruchomiony. Sprawdzanie bazy co 5s... [cite: 4]")
    while True: 
        task_id = claim_task()
        
        if task_id:
            print(f"Pobrano zadanie: {task_id}. Rozpoczynam pracę (30s)...")
            time.sleep(30)
            
            update_status(task_id, "done")
            print(f"Zadanie {task_id} zakończone (status: done).")
        else:
            time.sleep(5)

if __name__ == "__main__":
    consume()