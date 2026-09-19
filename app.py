import os
import requests
from flask import Flask, request, jsonify

app = Flask(__name__)

BOT_TOKEN = os.environ.get("BOT_TOKEN", "")
API = f"https://api.telegram.org/bot{BOT_TOKEN}"


def tg(method, data):
    try:
        response = requests.post(
            f"{API}/{method}",
            json=data,
            timeout=30
        )
        return response.json()
    except Exception as e:
        print("Telegram Error:", e)
        return {}


@app.route("/", methods=["GET"])
def home():
    return "International New Bot is running", 200


@app.route("/webhook", methods=["POST"])
def webhook():
    update = request.get_json(silent=True) or {}

    message = update.get("message")

    if message:
        chat_id = message["chat"]["id"]

        if message.get("voice"):
            file_id = message["voice"]["file_id"]

            tg("sendMessage", {
                "chat_id": chat_id,
                "text": f"VOICE_FILE_ID:\n{file_id}"
            })

            return jsonify({"ok": True}), 200

        tg("sendMessage", {
            "chat_id": chat_id,
            "text": "ابعت التسجيل الصوتي هنا عشان أطلع الـ File ID."
        })

        return jsonify({"ok": True}), 200

    return jsonify({"ok": True}), 200
