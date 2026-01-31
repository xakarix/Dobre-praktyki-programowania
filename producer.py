import uuid
import sys

def create_task(filename="tasks.txt"):
    task_id = uuid.uuid4()
    task_line = f"id: {task_id}, status: pending\n"

    with open(filename, "a") as file:
        file.write(task_line)

    print(f"Producent: Zapisano zadanie {task_id} do kolejki.")

if __name__ == "__main__":
    count = 1
    if len(sys.argv) > 1:
        count = int(sys.argv[1])
    
    for _ in range(count):
        create_task()