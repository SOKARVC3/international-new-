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


def telegram(method, data):
    try:
        response = requests.post(
            f"{API}/{method}",
            json=data,
            timeout=30
        )

        result = response.json()
        print("TELEGRAM:", method, result)

        return result

    except Exception as e:
        print("TELEGRAM ERROR:", repr(e))
        return {}


def redis_get(key):
    if not REDIS_URL or not REDIS_TOKEN:
        print("REDIS CONFIG MISSING")
        return None

    try:
        response = requests.get(
            f"{REDIS_URL}/get/{quote(key, safe='')}",
            headers={
                "Authorization": f"Bearer {REDIS_TOKEN}"
            },
            timeout=10
        )

        print("REDIS GET:", response.status_code, response.text)

        return response.json()

    except Exception as e:
        print("REDIS GET ERROR:", repr(e))
        return None


def redis_set(key):
    if not REDIS_URL or not REDIS_TOKEN:
        print("REDIS CONFIG MISSING")
        return False

    try:
        response = requests.post(
            f"{REDIS_URL}/set/{quote(key, safe='')}/1",
            headers={
                "Authorization": f"Bearer {REDIS_TOKEN}"
            },
            timeout=10
        )

        print("REDIS SET:", response.status_code, response.text)

        return response.ok

    except Exception as e:
        print("REDIS SET ERROR:", repr(e))
        return False


def already_welcomed(key):
    result = redis_get(key)

    if result and result.get("result") == "1":
        print("ALREADY WELCOMED:", key)
        return True

    print("NEW PERSON:", key)
    return False


def send_welcome(chat_id, business_connection_id=None):

    text_data = {
        "chat_id": chat_id,
        "text": REPLY_TEXT
    }

    if business_connection_id:
        text_data["business_connection_id"] = business_connection_id

    telegram("sendMessage", text_data)

    if AUDIO_FILE_ID:

        audio_data = {
            "chat_id": chat_id,
            "audio": AUDIO_FILE_ID
        }

        if business_connection_id:
            audio_data["business_connection_id"] = business_connection_id

        telegram("sendAudio", audio_data)


@app.route("/", methods=["GET"])
def home():

    if BOT_TOKEN:
        telegram("setWebhook", {
            "url": WEBHOOK_URL,
            "allowed_updates": [
                "message",
                "business_message"
            ]
        })

    return "International New Bot is running", 200


@app.route("/webhook", methods=["POST"])
def webhook():

    update = request.get_json(silent=True) or {}

    print("UPDATE RECEIVED")

    message = update.get("message")

    if message:

        chat_id = message["chat"]["id"]

        key = f"welcome:normal:{chat_id}"

        if already_welcomed(key):
            return jsonify({"ok": True}), 200

        send_welcome(chat_id)

        redis_set(key)

        return jsonify({"ok": True}), 200


    business_message = update.get("business_message")

    if business_message:

        chat_id = business_message["chat"]["id"]

        business_connection_id = business_message.get(
            "business_connection_id"
        )

        key = f"welcome:business:{business_connection_id}:{chat_id}"

        print("BUSINESS KEY:", key)

        if already_welcomed(key):
            return jsonify({"ok": True}), 200

        send_welcome(
            chat_id,
            business_connection_id
        )

        redis_set(key)

        return jsonify({"ok": True}), 200


    return jsonify({"ok": True}), 200
