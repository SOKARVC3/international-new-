import os
import requests
from urllib.parse import quote
from flask import Flask, request, jsonify

app = Flask(__name__)

BOT_TOKEN = os.environ.get("BOT_TOKEN", "")
AUDIO_FILE_ID = os.environ.get("AUDIO_FILE_ID", "")

REDIS_URL = os.environ.get("UPSTASH_REDIS_REST_URL", "").rstrip("/")
REDIS_TOKEN = os.environ.get("UPSTASH_REDIS_REST_TOKEN", "")

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


def already_welcomed(key):
    if not REDIS_URL or not REDIS_TOKEN:
        return False

    try:
        response = requests.get(
            f"{REDIS_URL}/get/{quote(key, safe='')}",
            headers={
                "Authorization": f"Bearer {REDIS_TOKEN}"
            },
            timeout=10
        )

        data = response.json()
        return data.get("result") == "1"

    except Exception as e:
        print("Redis GET Error:", e)
        return False


def mark_welcomed(key):
    if not REDIS_URL or not REDIS_TOKEN:
        return

    try:
        requests.post(
            f"{REDIS_URL}/set/{quote(key, safe='')}/1",
            headers={
                "Authorization": f"Bearer {REDIS_TOKEN}"
            },
            timeout=10
        )

    except Exception as e:
        print("Redis SET Error:", e)


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
    business_message = update.get("business_message")

    if message:
        chat_id = message["chat"]["id"]

        key = f"welcome:normal:{chat_id}"

        if already_welcomed(key):
            return jsonify({"ok": True}), 200

        tg("sendMessage", {
            "chat_id": chat_id,
            "text": REPLY_TEXT
        })

        if AUDIO_FILE_ID:
            tg("sendAudio", {
                "chat_id": chat_id,
                "audio": AUDIO_FILE_ID
            })

        mark_welcomed(key)

        return jsonify({"ok": True}), 200

    if business_message:
        chat_id = business_message["chat"]["id"]
        business_connection_id = business_message.get(
            "business_connection_id"
        )

        key = f"welcome:business:{business_connection_id}:{chat_id}"

        if already_welcomed(key):
            return jsonify({"ok": True}), 200

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

        mark_welcomed(key)

        return jsonify({"ok": True}), 200

    return jsonify({"ok": True}), 200
