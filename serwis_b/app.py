import pika
import os
import json
import logging
from flask import Flask, request, jsonify

app = Flask(__name__)
logging.basicConfig(level=logging.INFO)

RABBITMQ_HOST = os.environ.get("RABBITMQ_HOST", "localhost")
QUEUE_NAME = "ai_tasks"


def send_to_rabbit(task_data):
    connection = pika.BlockingConnection(pika.ConnectionParameters(host=RABBITMQ_HOST))
    channel = connection.channel()
    channel.queue_declare(queue=QUEUE_NAME, durable=True)  # Kolejka trwała

    channel.basic_publish(
        exchange="",
        routing_key=QUEUE_NAME,
        body=json.dumps(task_data),
        properties=pika.BasicProperties(
            delivery_mode=2,  # zapis na dysku
        ),
    )
    connection.close()


@app.route("/analyze", methods=["POST"])
def analyze():
    url = request.json.get("url")
    if not url:
        return jsonify({"error": "URL required"}), 400

    try:
        send_to_rabbit({"url": url})
        logging.info(f"Przesłano: {url}")
        return jsonify({"status": "queued", "message": "Processing started"}), 202 #accepeted
    except Exception as e:
        logging.error(f"RabbitMQ Error: {e}")
        return jsonify({"error": "Queue service unavailable"}), 503


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
