import os
import requests


GRAPH_API_URL = "https://graph.facebook.com/v21.0"


def send_reply(to: str, body: str) -> dict:
    """Send a text message back to the user via WhatsApp Cloud API.

    Args:
        to: Recipient phone number in international format (e.g. "15551234567").
        body: The text message to send.

    Returns:
        The JSON response from the API, or an error dict on failure.
    """
    token = os.getenv("WHATSAPP_TOKEN")
    phone_number_id = os.getenv("PHONE_NUMBER_ID")

    if not token or not phone_number_id:
        return {"error": "WHATSAPP_TOKEN or PHONE_NUMBER_ID not set"}

    url = f"{GRAPH_API_URL}/{phone_number_id}/messages"

    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    }

    payload = {
        "messaging_product": "whatsapp",
        "recipient_type": "individual",
        "to": to,
        "type": "text",
        "text": {"preview_url": False, "body": body},
    }

    try:
        resp = requests.post(url, headers=headers, json=payload, timeout=10)
        resp.raise_for_status()
        return resp.json()
    except requests.RequestException as exc:
        return {"error": str(exc)}
