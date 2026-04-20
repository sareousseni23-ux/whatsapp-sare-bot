"""Message routing logic — translated to Italian and French."""

from calendar_integration import get_upcoming_events
from slack_integration import get_recent_action_items


def handle_message(text: str) -> str:
    """Route an incoming message to the appropriate skill and return a reply."""
    normalised = text.strip().lower()

    if _matches_faq(normalised):
        return faq_skill(text)
    if _matches_calendar(normalised):
        return calendar_skill(text)
    if _matches_slack(normalised):
        return slack_skill(text)
    if _matches_crm(normalised):
        return crm_skill(text)

    return (
        "😐 Scusa, non ho capito. Prova a chiedermi del calendario, dei task su Slack o delle FAQ.\n\n"
        "Désolé, je n'ai pas compris. Essayez de me poser des questions sur le calendrier, les tâches Slack ou la FAQ."
    )


# ── keyword matchers ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

FAQ_KEYWORDS = {"faq", "aiuto", "aide", "info", "prezzi", "prix", "orari", "horaires"}
CALENDAR_KEYWORDS = {"calendario", "calendrier", "agenda", "impegni", "rendez-vous", "appuntamento", "book", "prenota"}
SLACK_KEYWORDS = {"slack", "task", "todo", "compiti", "tâches", "da fare", "messaggi"}
CRM_KEYWORDS = {"crm", "contatto", "contact", "lead", "cliente", "client", "pipeline"}


def _matches_faq(text: str) -> bool:
    return any(kw in text for kw in FAQ_KEYWORDS)


def _matches_calendar(text: str) -> bool:
    return any(kw in text for kw in CALENDAR_KEYWORDS)


def _matches_slack(text: str) -> bool:
    return any(kw in text for kw in SLACK_KEYWORDS)


def _matches_crm(text: str) -> bool:
    return any(kw in text for kw in CRM_KEYWORDS)


# ── skill responses ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def faq_skill(text: str) -> str:
    return (
        "📖 *FAQ SARE*\n\n"
        "Orari: Lun–Ven 9:00 – 18:00 UTC.\n"
        "Horaires: Lun–Ven 9h00 – 18h00 UTC.\n\n"
        "Sito: https://example.com/pricing"
    )


def calendar_skill(text: str) -> str:
    events = get_upcoming_events()
    if not events:
        return (
            "📅 *Calendario*\n\n"
            "Nessun impegno trovato per il resto della settimana.\n"
            "Aucun événement trouvé pour le reste de la semaine."
        )

    lines = []
    for ev in events:
        lines.append(f"• *{ev['title']}* — {ev['start']}")

    event_list = "\n".join(lines)
    return f"📅 *I tuoi impegni:*\n\n{event_list}"


def slack_skill(text: str) -> str:
    items = get_recent_action_items()
    if not items:
        return (
            "📋 *Slack Task*\n\n"
            "Non ho trovato nuovi task o messaggi importanti su Slack.\n"
            "Aucune tâche trouvée sur Slack."
        )

    lines = []
    for item in items:
        msg = item['text'][:100] + "..." if len(item['text']) > 100 else item['text']
        lines.append(f"• *#{item['channel']}*: {msg}")

    item_list = "\n".join(lines)
    return f"📋 *Task trovati su Slack:*\n\n{item_list}"


def crm_skill(text: str) -> str:
    return (
        "👤 *CRM SARE*\n\n"
        "Hai 3 trattative aperte per un totale di $42.000.\n"
        "Vous avez 3 opportunités ouvertes pour un total de 42 000 $."
    )
