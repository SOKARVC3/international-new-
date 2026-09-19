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

        # لو الرسالة تسجيل صوتي
        if message.get("voice"):
            file_id = message["voice"]["file_id"]

            tg("sendMessage", {
                "chat_id": chat_id,
                "text": f"VOICE_FILE_ID:\n{file_id}"
            })

            return jsonify({"ok": True}), 200

        # لو أي رسالة عادية
        tg("sendMessage", {
            "chat_id": chat_id,
            "text": "ابعت التسجيل الصوتي هنا عشان أطلع الـ File ID."
        })

        return jsonify({"ok": True}), 200

    return jsonify({"ok": True}), 200


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
    # =========================
    # رسائل التليجرام العادية
    # =========================
    message = update.get("message")

    if message:
        chat_id = message["chat"]["id"]

        # إرسال الرسالة الكتابية
        tg("sendMessage", {
            "chat_id": chat_id,
            "text": REPLY_TEXT
        })

        # إرسال التسجيل الصوتي
        if VOICE_FILE_ID:
            tg("sendVoice", {
                "chat_id": chat_id,
                "voice": VOICE_FILE_ID
            })

        return jsonify({"ok": True}), 200

    # =========================
    # رسائل Telegram Business
    # =========================
    business_message = update.get("business_message")

    if business_message:
        chat_id = business_message["chat"]["id"]
        business_connection_id = business_message.get(
            "business_connection_id"
        )

        # إرسال الرسالة الكتابية
        text_data = {
            "chat_id": chat_id,
            "text": REPLY_TEXT
        }

        if business_connection_id:
            text_data["business_connection_id"] = business_connection_id

        tg("sendMessage", text_data)

        # إرسال التسجيل الصوتي
        if VOICE_FILE_ID:
            voice_data = {
                "chat_id": chat_id,
                "voice": VOICE_FILE_ID
            }

            if business_connection_id:
                voice_data["business_connection_id"] = business_connection_id

            tg("sendVoice", voice_data)

        return jsonify({"ok": True}), 200

    return jsonify({"ok": True}), 200


def set_webhook():
    if not BOT_TOKEN or not VERCEL_URL:
        print("BOT_TOKEN or VERCEL_URL is missing")
        return

    webhook_url = f"https://{VERCEL_URL}/webhook"

    result = tg("setWebhook", {
        "url": webhook_url,
        "allowed_updates": [
            "message",
            "business_message"
        ]
    })

    print("Webhook:", result)


# Vercel يشغل Flask مباشرة
if VERCEL_URL:
    set_webhook()


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(
        host="0.0.0.0",
        port=port
    )
