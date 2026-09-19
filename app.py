import os
import requests
from flask import Flask, request, jsonify

app = Flask(__name__)

BOT_TOKEN = os.environ.get("BOT_TOKEN", "")
AUDIO_FILE_ID = os.environ.get("AUDIO_FILE_ID", "")

API = f"https://api.telegram.org/bot{BOT_TOKEN}"

WEBHOOK_URL = "https://international-new.vercel.app/webhook"

REPLY_TEXT = "اسمع وأي استفسار بخصوص الشغل أنا معاك/ي"


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


def set_webhook():
    if BOT_TOKEN:
        result = tg("setWebhook", {
            "url": WEBHOOK_URL,
            "allowed_updates": [
                "message",
                "business_message"
            ]
        })
        print("Webhook:", result)


@app.route("/", methods=["GET"])
def home():
    set_webhook()
    return "International New Bot is running", 200


@app.route("/webhook", methods=["POST"])
def webhook():
    update = request.get_json(silent=True) or {}

    message = update.get("message")

    if message:
        chat_id = message["chat"]["id"]

        tg("sendMessage", {
            "chat_id": chat_id,
            "text": REPLY_TEXT
        })

        if AUDIO_FILE_ID:
            tg("sendAudio", {
                "chat_id": chat_id,
                "audio": AUDIO_FILE_ID
            })

        return jsonify({"ok": True}), 200

    business_message = update.get("business_message")

    if business_message:
        chat_id = business_message["chat"]["id"]
        business_connection_id = business_message.get(
            "business_connection_id"
        )

        text_data = {
            "chat_id": chat_id,
            "text": REPLY_TEXT
        }

        if business_connection_id:
            text_data["business_connection_id"] = business_connection_id

        tg("sendMessage", text_data)

        if AUDIO_FILE_ID:
            audio_data = {
                "chat_id": chat_id,
                "audio": AUDIO_FILE_ID
            }

            if business_connection_id:
                audio_data["business_connection_id"] = business_connection_id

            tg("sendAudio", audio_data)

        return jsonify({"ok": True}), 200

    return jsonify({"ok": True}), 200
