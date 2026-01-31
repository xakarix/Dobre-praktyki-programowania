import sqlite3
import os
import logging
from flask import Flask, request, jsonify

app = Flask(__name__)
logging.basicConfig(level=logging.INFO)

DB_PATH = os.environ.get("DB_PATH", "/data/results.db")


def init_db():
    try:
        os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)

        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS results (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                source_url TEXT NOT NULL,
                people_count INTEGER NOT NULL,
                processed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """
        )
        conn.commit()
        conn.close()
        logging.info(f"Baza danych gotowa: {DB_PATH}")
    except Exception as e:
        logging.error(f"Błąd inicjalizacji DB: {e}")


init_db()


@app.route("/results", methods=["POST"])
def save_result():
    data = request.json
    if not data or "source_url" not in data or "people_count" not in data:
        return jsonify({"error": "Invalid data"}), 400

    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO results (source_url, people_count) VALUES (?, ?)",
            (data["source_url"], data["people_count"]),
        )
        conn.commit()
        new_id = cursor.lastrowid
        conn.close()

        logging.info(f"Zapisano wynik. ID: {new_id} dla URL: {data['source_url']}")
        return jsonify({"status": "saved", "id": new_id}), 201 #created
    except Exception as e:
        logging.error(f"Błąd zapisu SQL: {e}")
        return jsonify({"error": "Internal DB Error"}), 500


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)