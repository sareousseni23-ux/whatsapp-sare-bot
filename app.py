"""Flask application — WhatsApp Cloud API webhook."""

import os

from dotenv import load_dotenv
from flask import Flask, request, jsonify

from logic import handle_message
from whatsapp_api import send_reply

load_dotenv()

app = Flask(__name__)

VERIFY_TOKEN = os.getenv("VERIFY_TOKEN", "my_secret_verify_token")


@app.route("/webhook", methods=["GET"])
def verify_webhook():
    """Hub verification — Meta sends a GET with challenge params."""
    mode = request.args.get("hub.mode")
    token = request.args.get("hub.verify_token")
    challenge = request.args.get("hub.challenge")

    if mode == "subscribe" and token == VERIFY_TOKEN:
        return challenge, 200
    return "Forbidden", 403


@app.route("/webhook", methods=["POST"])
def receive_message():
    """Process inbound WhatsApp messages and reply."""
    data = request.get_json(silent=True)
    if not data:
        return jsonify({"status": "ignored", "reason": "no JSON body"}), 400

    messages = _extract_messages(data)
    for msg in messages:
        sender = msg.get("from", "")
        text = msg.get("text", {}).get("body", "")
        if not text:
            continue

        reply_text = handle_message(text)
        send_reply(sender, reply_text)

    return jsonify({"status": "ok"}), 200


def _extract_messages(payload: dict) -> list:
    """Safely walk the nested webhook payload to pull out messages."""
    try:
        entries = payload.get("entry", [])
        messages = []
        for entry in entries:
            for change in entry.get("changes", []):
                value = change.get("value", {})
                messages.extend(value.get("messages", []))
        return messages
    except (AttributeError, TypeError):
        return []


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
