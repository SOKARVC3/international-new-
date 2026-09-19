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
        r = requests.post(
            f"{API}/{method}",
            json=data,
            timeout=30
        )
        result = r.json()
        print("TELEGRAM:", method, result)
        return result
    except Exception as e:
        print("TELEGRAM ERROR:", repr(e))
        return {}


def redis_command(command, *args):
    if not REDIS_URL or not REDIS_TOKEN:
        print("REDIS CONFIG MISSING")
        return None

    try:
        url = f"{REDIS_URL}/{command}"

        if args:
            url += "/" + "/".join(
                quote(str(x), safe="")
                for x in args
            )

        r = requests.post(
            url,
            headers={
                "Authorization": f"Bearer {REDIS_TOKEN}"
            },
            timeout=10
        )

        print("REDIS:", command, r.status_code, r.text)
        return r.json()

    except Exception as e:
        print("REDIS ERROR:", repr(e))
        return None


def already_welcomed(key):
    result = redis_command("get", key)

    if result and result.get("result") == "1":
        print("ALREADY WELCOMED:", key)
        return True

    print("NOT WELCOMED:", key)
    return False


def mark_welcomed(key):
    result = redis_command("set", key, "1")

    if result and result.get("result") == "OK":
        print("WELCOME SAVED:", key)
        return True

    print("WELCOME SAVE FAILED:", key)
    return False


def send_welcome(chat_id, business_connection_id=None):
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


@app.route("/", methods=["GET"])
def home():
    if BOT_TOKEN:
        tg("setWebhook", {
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

    print("UPDATE RECEIVED:", update)

    message = update.get("message")
    business_message = update.get("business_message")

    if message:
        chat_id = message["chat"]["id"]
        key = f"welcome:normal:{chat_id}"

        if already_welcomed(key):
            return jsonify({"ok": True}), 200

        send_welcome(chat_id)

        mark_welcomed(key)

        return jsonify({"ok": True}), 200

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

        mark_welcomed(key)

        return jsonify({"ok": True}), 200

    return jsonify({"ok": True}), 200
