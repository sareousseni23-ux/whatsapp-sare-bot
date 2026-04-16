"""Google Calendar integration via Composio SDK."""

import os
import logging
from datetime import datetime, timezone

from composio import Composio

logger = logging.getLogger(__name__)


def get_upcoming_events() -> list[dict]:
    """Fetch upcoming Google Calendar events from now until 2026-04-19T23:59:59Z.

    Returns a list of dicts with keys 'title' and 'start'.
    Returns an empty list if no events are found or an error occurs.
    """
    api_key = os.getenv("COMPOSIO_API_KEY")
    if not api_key:
        logger.error("COMPOSIO_API_KEY is not set")
        return []

    time_min = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    time_max = "2026-04-19T23:59:59Z"

    try:
        client = Composio(api_key=api_key)
        response = client.tools.execute(
            "GOOGLECALENDAR_EVENTS_LIST",
            arguments={
                "calendarId": "primary",
                "timeMin": time_min,
                "timeMax": time_max,
                "singleEvents": True,
                "orderBy": "startTime",
                "maxResults": 50,
            },
        )

        response_data = response if isinstance(response, dict) else getattr(response, "data", {})
        items = response_data.get("items", response_data.get("data", {}).get("items", []))

        if not items:
            return []

        events = []
        for item in items:
            title = item.get("summary", "No title")
            start_info = item.get("start", {})
            start = start_info.get("dateTime", start_info.get("date", "Unknown"))
            events.append({"title": title, "start": start})

        return events

    except Exception as exc:
        logger.exception("Failed to fetch calendar events: %s", exc)
        return []
