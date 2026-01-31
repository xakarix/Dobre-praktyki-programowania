import pika
import requests
import json
import time
import os
import logging
from ultralytics import YOLO

logging.basicConfig(level=logging.INFO, format="%(asctime)s - WORKER - %(message)s")

RABBITMQ_HOST = os.environ.get("RABBITMQ_HOST", "localhost")
SERVICE_A_URL = os.environ.get("SERVICE_A_URL", "http://localhost:5001/results")
QUEUE_NAME = "ai_tasks"

# ładowanie modelu
logging.info("Ładowanie modelu YOLOv8n")
model = YOLO("yolov8n.pt")
logging.info("Model YOLOv8n załadowany.")


def count_people_yolo(url):
    logging.info(f"ananliz YOLO dla: {url}")

    try:
        results = model.predict(source=url, save=False, verbose=False)

        result = results[0]
        classes = result.boxes.cls
        # 0 to numer człowieka, zlicza ile jest 0
        people_count = (classes == 0).sum().item()

        return people_count

    except Exception as e:
        logging.error(f"Błąd wewnątrz YOLO: {e}")
        raise e


# wywałoana za kadym razem do rabbit ma zadanko
def callback(ch, method, properties, body):
    data = json.loads(body)
    url = data.get("url")

    logging.info(f"--> Odebrano zadanie: {url}")

    try:
        count = count_people_yolo(url)

        # wysyłka do serwisu a
        payload = {"source_url": url, "people_count": count}

        logging.info(f"Liczba osob: {count}. Wysyłanie do Serwisu A...")
        response = requests.post(SERVICE_A_URL, json=payload, timeout=5)

        if response.status_code in [200, 201]:  # done, created
            logging.info(" [SUCCESS] Wynik zapisany.")
            ch.basic_ack(delivery_tag=method.delivery_tag)
        else:
            logging.warning(
                f" [FAIL] Serwis A error {response.status_code}. Ponawiam..."
            )
            time.sleep(2)
            ch.basic_nack(delivery_tag=method.delivery_tag, requeue=True)

    except requests.exceptions.RequestException as e:
        logging.error(f" [NETWORK ERROR] Brak połączenia z Serwisem A: {e}")
        time.sleep(5)
        ch.basic_nack(delivery_tag=method.delivery_tag, requeue=True)

    except Exception as e:
        logging.error(f" [AI ERROR] Błąd przetwarzania obrazu: {e}")
        ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False)


def start_worker():
    while True:
        try:
            connection = pika.BlockingConnection(
                pika.ConnectionParameters(host=RABBITMQ_HOST)
            )
            channel = connection.channel()
            channel.queue_declare(queue=QUEUE_NAME, durable=True)
            channel.basic_qos(prefetch_count=1)
            channel.basic_consume(
                queue=QUEUE_NAME, on_message_callback=callback, auto_ack=False
            )

            logging.info(" [*] Worker gotowy. Oczekiwanie na zadania..")
            channel.start_consuming()

        except pika.exceptions.AMQPConnectionError:
            logging.info("Brak połączenia z RabbitMQ. ponowna próba za 5s...")
            time.sleep(5)


if __name__ == "__main__":
    start_worker()
