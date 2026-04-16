"""Message routing logic — inspects incoming text and dispatches to skill handlers."""


def handle_message(text: str) -> str:
    """Route an incoming message to the appropriate skill and return a reply.

    Routing rules (checked in order):
        • FAQ keywords  → faq_skill
        • Calendar keywords → calendar_skill
        • CRM keywords  → crm_skill
        • Anything else → default reply
    """
    normalised = text.strip().lower()

    if _matches_faq(normalised):
        return faq_skill(text)
    if _matches_calendar(normalised):
        return calendar_skill(text)
    if _matches_crm(normalised):
        return crm_skill(text)

    return (
        "Sorry, I didn't understand that. "
        "Try asking about our FAQ, your calendar, or CRM contacts."
    )


# ── keyword matchers ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

FAQ_KEYWORDS = {"faq", "help", "question", "support", "info", "hours", "pricing"}
CALENDAR_KEYWORDS = {"calendar", "schedule", "meeting", "appointment", "event", "book"}
CRM_KEYWORDS = {"crm", "contact", "lead", "customer", "deal", "pipeline", "account"}


def _matches_faq(text: str) -> bool:
    return any(kw in text for kw in FAQ_KEYWORDS)


def _matches_calendar(text: str) -> bool:
    return any(kw in text for kw in CALENDAR_KEYWORDS)


def _matches_crm(text: str) -> bool:
    return any(kw in text for kw in CRM_KEYWORDS)


# ── skill placeholders ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def faq_skill(text: str) -> str:
    """Placeholder — look up an answer from the FAQ knowledge base."""
    return (
        "📖 *FAQ Skill*\n"
        f"You asked: _{text}_\n\n"
        "Our business hours are Mon–Fri 9 AM – 6 PM UTC.\n"
        "For detailed pricing visit https://example.com/pricing."
    )


def calendar_skill(text: str) -> str:
    """Placeholder — create, list, or modify calendar events."""
    return (
        "📅 *Calendar Skill*\n"
        f"You asked: _{text}_\n\n"
        "Your next meeting is tomorrow at 10:00 AM with the product team.\n"
        "Reply with *book <title> <date> <time>* to schedule a new event."
    )


def crm_skill(text: str) -> str:
    """Placeholder — query or update CRM records."""
    return (
        "👤 *CRM Skill*\n"
        f"You asked: _{text}_\n\n"
        "Found 3 open deals in your pipeline totalling $42,000.\n"
        "Reply with *contact <name>* to look up a specific record."
    )
