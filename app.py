import os
import requests
from flask import Flask, request

app = Flask(__name__)

BOT_TOKEN = os.environ["BOT_TOKEN"]
VOICE_FILE_ID = os.environ.get("VOICE_FILE_ID", "")
RENDER_URL = os.environ.get("RENDER_EXTERNAL_URL", "")

API = f"https://api.telegram.org/bot{BOT_TOKEN}"


def tg(method, data):
    return requests.post(
        f"{API}/{method}",
        data=data,
        timeout=30
    )


@app.route("/", methods=["GET"])
def home():
    return "International New Bot is running"


@app.route("/webhook", methods=["POST"])
def webhook():
    update = request.get_json(silent=True) or {}

    # لو بعت التسجيل الصوتي للبوت نفسه
    msg = update.get("message")

    if msg and msg.get("voice"):
        file_id = msg["voice"]["file_id"]

        tg("sendMessage", {
            "chat_id": msg["chat"]["id"],
            "text": f"تم استلام التسجيل.\nVOICE_FILE_ID:\n{file_id}"
        })

        return "OK"

    # رسالة جديدة على حسابك الشخصي المرتبط بالبوت
    business_msg = update.get("business_message")

    if business_msg:
        business_connection_id = business_msg.get(
            "business_connection_id"
        )

        chat_id = business_msg["chat"]["id"]

        # الرسالة الكتابية
        tg("sendMessage", {
            "business_connection_id": business_connection_id,
            "chat_id": chat_id,
            "text": "اسمع، وأي استفسار بخصوص الشغل أنا معاك/ي."
        })

        # التسجيل الصوتي
        if VOICE_FILE_ID:
            tg("sendVoice", {
                "business_connection_id": business_connection_id,
                "chat_id": chat_id,
                "voice": VOICE_FILE_ID
            })

    return "OK"


def set_webhook():
    if RENDER_URL:
        webhook_url = RENDER_URL.rstrip("/") + "/webhook"

        tg("setWebhook", {
            "url": webhook_url,
            "allowed_updates": '["message","business_message"]'
        })


if __name__ == "__main__":
    set_webhook()

    port = int(os.environ.get("PORT", 10000))
    app.run(
        host="0.0.0.0",
        port=port
)
