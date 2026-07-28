import time
import logging
import requests
from typing import TypedDict
from langgraph.graph import StateGraph, END

logger = logging.getLogger("lead-engine.outreach")

GEMINI_MODEL = "gemini-2.0-flash"
GEMINI_URL = (
    f"https://generativelanguage.googleapis.com/v1beta/models/"
    f"{GEMINI_MODEL}:generateContent"
)


class OutreachState(TypedDict):
    lead: dict
    channel: str    # "whatsapp" | "email"
    message: str
    subject: str


# ── Node 1: Choose channel ────────────────────────────────────────────────────
def choose_channel(state: OutreachState) -> OutreachState:
    lead = state["lead"]
    has_real_phone = bool(lead.get("phone"))
    state["channel"] = "whatsapp" if has_real_phone else "email"
    logger.info(f"Outreach channel for {lead.get('email')}: {state['channel']}")
    return state


# ── Node 2: Generate personalised message via Gemini ─────────────────────────
def generate_message(state: OutreachState) -> OutreachState:
    from src.app.core.settings import settings

    lead = state["lead"]
    channel = state["channel"]
    name = lead.get("name", "there")
    category = lead.get("title", "your business")
    ai_reason = lead.get("ai_reason", "")

    length_guide = (
        "Keep it under 160 characters. Friendly, informal tone."
        if channel == "whatsapp"
        else "Write 3-4 sentences. Professional but warm tone."
    )

    prompt = f"""You are writing a cold outreach message for a digital marketing & AI automation agency.

Target:
- Business: {name}
- Industry: {category}
- Why we're reaching out: {ai_reason or 'they look like a strong prospect for AI automation services'}

Channel: {channel}
{length_guide}

Write ONLY the message body. No subject line. No extra explanation."""

    subject = f"Quick question about {name}"

    try:
        if not settings.GEMINI_API_KEY:
            raise RuntimeError("No Gemini key")

        response = requests.post(
            GEMINI_URL,
            params={"key": settings.GEMINI_API_KEY},
            json={"contents": [{"parts": [{"text": prompt}]}]},
            timeout=10,
        )
        response.raise_for_status()
        message = response.json()["candidates"][0]["content"]["parts"][0]["text"].strip()
        logger.info(f"Gemini generated {channel} message for '{name}'")

    except Exception as e:
        logger.warning(f"Gemini message generation failed ({e}) — using template")
        if channel == "whatsapp":
            message = (
                f"Hi {name}! We help {category} businesses grow with AI automation. "
                f"Can we connect for a quick chat?"
            )
        else:
            message = (
                f"Hi {name},\n\n"
                f"We specialise in helping {category} businesses save time and increase revenue "
                f"with AI automation. I'd love to show you what we've built for similar businesses.\n\n"
                f"Would you be open to a quick 10-minute call this week?\n\nBest regards"
            )

    state["message"] = message
    state["subject"] = subject
    
    # Increased safety delay (6 seconds) to strictly respect Free-tier Gemini RPM limits
    logger.info("Pausing 6s to respect free-tier Gemini rate limits...")
    time.sleep(6.0)
    return state


# ── Node 3: Send ──────────────────────────────────────────────────────────────
def send_outreach(state: OutreachState) -> OutreachState:
    lead = state["lead"]
    message = state["message"]
    channel = state["channel"]

    if channel == "whatsapp":
        from src.app.services.whatsapp_service import WhatsAppService
        success = False
        attempts = 3
        
        for attempt in range(1, attempts + 1):
            try:
                svc = WhatsAppService()
                svc.send_message(phone=lead["phone"], message=message)
                logger.info(f"WhatsApp successfully sent to {lead['phone']}")
                success = True
                break
            except Exception as e:
                logger.warning(f"Attempt {attempt}/{attempts} failed for WhatsApp to {lead.get('phone')}: {e}")
                if attempt < attempts:
                    time.sleep(2.0)

        if not success:
            logger.error(f"WhatsApp permanently failed for {lead.get('phone')}. Falling back to email if available.")
            if lead.get("email") and "placeholder" not in lead.get("email", ""):
                logger.info(f"Falling back to email for {lead.get('email')}")
                _send_email(lead, state["subject"], message)
                state["channel"] = "email_fallback"
    else:
        _send_email(lead, state["subject"], message)

    return state


def _send_email(lead: dict, subject: str, message: str):
    from src.app.services.email_service import EmailService
    email = lead.get("email", "")
    if not email or "placeholder" in email or "noemail" in email:
        logger.info(f"Skipping email — no real email for {lead.get('name')}")
        return
    try:
        svc = EmailService()
        svc.send_email(recipient=email, subject=subject, content=message)
    except Exception as e:
        logger.error(f"Email failed for {email}: {e}")


# ── Graph ─────────────────────────────────────────────────────────────────────
def build_graph():
    graph = StateGraph(OutreachState)
    graph.add_node("choose_channel", choose_channel)
    graph.add_node("generate_message", generate_message)
    graph.add_node("send_outreach", send_outreach)
    graph.set_entry_point("choose_channel")
    graph.add_edge("choose_channel", "generate_message")
    graph.add_edge("generate_message", "send_outreach")
    graph.add_edge("send_outreach", END)
    return graph.compile()


outreach_graph = build_graph()
