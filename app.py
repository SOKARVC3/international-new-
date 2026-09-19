import os
import requests
from flask import Flask, request, jsonify

app = Flask(__name__)

BOT_TOKEN = os.environ.get("BOT_TOKEN", "")
API = f"https://api.telegram.org/bot{BOT_TOKEN}"

WEBHOOK_URL = "https://international-new.vercel.app/webhook"


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

        # Voice message
        if message.get("voice"):
            file_id = message["voice"]["file_id"]

            tg("sendMessage", {
                "chat_id": chat_id,
                "text": f"VOICE_FILE_ID:\n{file_id}"
            })

            return jsonify({"ok": True}), 200

        # Audio file
        if message.get("audio"):
            file_id = message["audio"]["file_id"]

            tg("sendMessage", {
                "chat_id": chat_id,
                "text": f"AUDIO_FILE_ID:\n{file_id}"
            })

            return jsonify({"ok": True}), 200

        tg("sendMessage", {
            "chat_id": chat_id,
            "text": "ابعت التسجيل الصوتي هنا."
        })

        return jsonify({"ok": True}), 200

    return jsonify({"ok": True}), 200
