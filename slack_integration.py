"""Slack integration via Composio SDK — fetches action items from public channels."""

import os
import re
import logging

from composio import Composio

logger = logging.getLogger(__name__)

TASK_PATTERNS = re.compile(
    r"(todo|task|da fare|action item|:white_check_mark:|✅)",
    re.IGNORECASE,
)


def get_recent_action_items() -> list[dict]:
    """Scan public Slack channels for messages that look like tasks.

    Returns a list of dicts with keys 'channel', 'text', and 'user'.
    Returns an empty list if no action items are found or an error occurs.
    """
    api_key = os.getenv("COMPOSIO_API_KEY")
    if not api_key:
        logger.error("COMPOSIO_API_KEY is not set")
        return []

    try:
        client = Composio(api_key=api_key)

        # 1. List public channels
        conv_response = client.tools.execute(
            "SLACK_LIST_CONVERSATIONS",
            arguments={
                "types": "public_channel",
                "exclude_archived": True,
                "limit": 100,
            },
        )

        channels = _extract_channels(conv_response)
        if not channels:
            return []

        # 2. Fetch last 20 messages from each channel and filter for tasks
        action_items = []
        for channel in channels:
            channel_id = channel.get("id", "")
            channel_name = channel.get("name", channel_id)

            try:
                hist_response = client.tools.execute(
                    "SLACK_FETCH_CONVERSATION_HISTORY",
                    arguments={
                        "channel": channel_id,
                        "limit": 20,
                    },
                )

                messages = _extract_messages(hist_response)
                for msg in messages:
                    text = msg.get("text", "")
                    if TASK_PATTERNS.search(text):
                        action_items.append({
                            "channel": channel_name,
                            "text": text,
                            "user": msg.get("user", "unknown"),
                        })
            except Exception as exc:
                logger.warning("Failed to fetch history for #%s: %s", channel_name, exc)
                continue

        return action_items

    except Exception as exc:
        logger.exception("Failed to fetch Slack action items: %s", exc)
        return []


def _extract_channels(response) -> list[dict]:
    """Pull the channel list out of the Composio response."""
    data = response if isinstance(response, dict) else getattr(response, "data", {})
    channels = data.get("channels", data.get("data", {}).get("channels", []))
    return channels if isinstance(channels, list) else []


def _extract_messages(response) -> list[dict]:
    """Pull messages out of the Composio conversation-history response."""
    data = response if isinstance(response, dict) else getattr(response, "data", {})
    messages = data.get("messages", data.get("data", {}).get("messages", []))
    return messages if isinstance(messages, list) else []
