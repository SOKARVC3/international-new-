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


def claim_user(chat_id):
    """
    يحجز الشخص مرة واحدة فقط.
    لو الشخص موجود بالفعل يرجع False.
    لو أول مرة يرجع True.
    """

    key = f"welcome:sent:{chat_id}"

    result = redis_command(
        "set",
        key,
        "1",
        "nx"
    )

    if result and result.get("result") == "OK":
        print("NEW USER - CLAIMED:", chat_id)
        return True

    print("USER ALREADY CLAIMED:", chat_id)
    return False


def remove_claim(chat_id):
    """
    لو حصل فشل قبل الإرسال، نلغي الحجز
    عشان نقدر نحاول مرة أخرى.
    """

    key = f"welcome:sent:{chat_id}"

    redis_command("del", key)

    print("CLAIM REMOVED:", chat_id)


def send_welcome(chat_id, business_connection_id=None):

    text_data = {
        "chat_id": chat_id,
        "text": REPLY_TEXT
    }

    if business_connection_id:
        text_data["business_connection_id"] = business_connection_id

    text_result = tg(
        "sendMessage",
        text_data
    )

    if not text_result.get("ok"):
        print("TEXT SEND FAILED")

        remove_claim(chat_id)

        return False

    if AUDIO_FILE_ID:

        audio_data = {
            "chat_id": chat_id,
            "audio": AUDIO_FILE_ID
        }

        if business_connection_id:
            audio_data["business_connection_id"] = business_connection_id

        audio_result = tg(
            "sendAudio",
            audio_data
        )

        if not audio_result.get("ok"):
            print("AUDIO SEND FAILED")

            # الرسالة النصية اتبعت بالفعل،
            # لذلك لا نحذف الحجز هنا.
            return True

    return True


@app.route("/", methods=["GET"])
def home():

    if BOT_TOKEN:

        tg(
            "setWebhook",
            {
                "url": WEBHOOK_URL,
                "allowed_updates": [
                    "message",
                    "business_message"
                ]
            }
        )

    return "International New Bot is running", 200


@app.route("/webhook", methods=["POST"])
def webhook():

    update = request.get_json(silent=True) or {}

    print("UPDATE RECEIVED:", update)

    message = update.get("message")
    business_message = update.get("business_message")

    # رسالة عادية
    if message:

        chat_id = message["chat"]["id"]

        print("NORMAL CHAT:", chat_id)

        # الشخص اتعامل معاه قبل كده؟
        if not claim_user(chat_id):

            return jsonify({
                "ok": True,
                "status": "already_sent"
            }), 200

        send_welcome(chat_id)

        return jsonify({
            "ok": True,
            "status": "sent"
        }), 200


    # رسالة Business
    if business_message:

        chat_id = business_message["chat"]["id"]

        business_connection_id = business_message.get(
            "business_connection_id"
        )

        print(
            "BUSINESS CHAT:",
            chat_id,
            "CONNECTION:",
            business_connection_id
        )

        # نفس الشخص = مرة واحدة فقط
        if not claim_user(chat_id):

            return jsonify({
                "ok": True,
                "status": "already_sent"
            }), 200

        send_welcome(
            chat_id,
            business_connection_id
        )

        return jsonify({
            "ok": True,
            "status": "sent"
        }), 200


    return jsonify({
        "ok": True,
        "status": "ignored"
    }), 200
