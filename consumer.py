import time
import os

filename = "tasks.txt"

def consume_tasks():
    print(f"Konsument uruchomiony. Oczekiwanie na zadania w {filename}...")
    
    while True:
        updated_tasks = []
        task_to_process = None
        
        try:
            if not os.path.exists(filename):
                print("Plik nie istnieje. Czekam...")
                time.sleep(5)
                continue

            with open(filename, "r") as file:
                tasks = file.readlines()

            for i, task in enumerate(tasks):
                if "status: pending" in task and task_to_process is None:
                    task_to_process = task
                    task_id = task.split(", ")[0].split(": ")[1]
                    tasks[i] = task.replace("pending", "in_progress")
                    print(f">>> Pobieram zadanie: {task_id}")
                updated_tasks.append(tasks[i])

            if task_to_process:
                with open(filename, "w") as file:
                    file.writelines(updated_tasks)
                
                task_id = task_to_process.split(", ")[0].split(": ")[1]
                print(f"Wykonywanie zadania {task_id} (potrwa 30s)...")
                time.sleep(30)

                with open(filename, "r") as file:
                    current_tasks = file.readlines()
                
                for i, t in enumerate(current_tasks):
                    if task_id in t and "in_progress" in t:
                        current_tasks[i] = t.replace("in_progress", "done")
                        break
                
                with open(filename, "w") as file:
                    file.writelines(current_tasks)
                
                print(f"V Zadanie {task_id} zostało zakończone!")
            else:
                # Brak zadań 'pending'
                print("Brak zadań do wykonania. Odpoczynek 5s...")
                time.sleep(5)

        except Exception as e:
            print(f"Wystąpił błąd: {e}")
            time.sleep(5)

if __name__ == "__main__":
    consume_tasks()