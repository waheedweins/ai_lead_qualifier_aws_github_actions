import logging
import requests
import traceback
from typing import TypedDict, List
from langgraph.graph import StateGraph, END

logger = logging.getLogger("lead-engine.services.langgraph_engine")

GEMINI_MODEL = "gemini-3.5-flash"
GEMINI_URL = (
    f"https://generativelanguage.googleapis.com/v1beta/models/"
    f"{GEMINI_MODEL}:generateContent"
)


# ── State ─────────────────────────────────────────────────────────────────────
class AgentState(TypedDict):
    lead: dict
    score: int               # last-write-wins; only "evaluate" ever sets this
    query: str
    results: List[dict]
    decision: str           # "hot" | "cold"
    reason: str             # Gemini's one-line explanation
    website_summary: str    # Tavily enrichment result


# ── Node 1: Tavily Website Enrichment ─────────────────────────────────────────
def enrich_with_tavily(state: AgentState) -> dict:
    """
    Searches the web for the business using Tavily and summarises findings.
    Gives Gemini richer context for scoring.
    Skips silently if TAVILY_API_KEY is not set.
    """
    from src.app.core.settings import settings

    lead = state.get("lead", {})
    business_name = lead.get("name", "")
    address = lead.get("address", "")
    website = lead.get("website", "")

    if not settings.TAVILY_API_KEY or not business_name:
        return {"website_summary": ""}

    try:
        query = website if website else f"{business_name} {address} business"
        response = requests.post(
            "https://api.tavily.com/search",
            json={
                "api_key": settings.TAVILY_API_KEY,
                "query": query,
                "search_depth": "basic",
                "max_results": 3,
                "include_answer": True,
            },
            timeout=10,
        )
        response.raise_for_status()
        data = response.json()

        parts = []
        if data.get("answer"):
            parts.append(data["answer"])
        for r in data.get("results", [])[:2]:
            if r.get("content"):
                parts.append(r["content"][:300])

        summary = " | ".join(parts)[:600]
        logger.info(f"Tavily enriched '{business_name}': {len(summary)} chars")
        return {"website_summary": summary}

    except Exception as e:
        logger.warning(f"Tavily enrichment skipped for '{business_name}': {e}")
        return {"website_summary": ""}


# ── Node 2: Gemini AI Scoring ─────────────────────────────────────────────────
def score_with_gemini(state: AgentState) -> dict:
    """
    Sends lead data to Gemini and gets a 0-100 score + one-line reason.
    Falls back to heuristic scoring if Gemini is unavailable.
    """
    from src.app.core.settings import settings

    lead = state.get("lead", {})
    website_summary = state.get("website_summary", "")

    web_context = (
        f"\nOnline presence: {website_summary}"
        if website_summary
        else "\nOnline presence: Not found"
    )

    prompt = f"""You are a B2B lead qualification expert for a digital marketing & AI automation agency.

Score this business lead 0-100 on likelihood to buy AI automation or digital marketing services.

Scoring guide (add points):
- Has phone number → +25 (WhatsApp reachable)
- Has real email (not placeholder) → +20
- Has physical address → +15
- Clear business name → +10
- Known industry/category → +10
- Online presence found → +10
- Established business (website, reviews) → +10

Lead data:
- Name: {lead.get('name', 'unknown')}
- Email: {lead.get('email', 'none')}
- Phone: {lead.get('phone', 'none')}
- Address: {lead.get('address', 'none')}
- Category: {lead.get('title', lead.get('source', 'none'))}
- Website: {lead.get('website', 'none')}{web_context}

Reply in EXACTLY this format (nothing else):
SCORE: <0-100>
REASON: <one sentence>"""

    try:
        if not settings.GEMINI_API_KEY:
            raise RuntimeError("GEMINI_API_KEY not configured")

        response = requests.post(
            GEMINI_URL,
            params={"key": settings.GEMINI_API_KEY},
            json={"contents": [{"parts": [{"text": prompt}]}]},
            timeout=15,
        )
        response.raise_for_status()
        text = response.json()["candidates"][0]["content"]["parts"][0]["text"]

        score, reason = 50, "Gemini scored this lead"
        for line in text.strip().splitlines():
            line = line.strip()
            if line.startswith("SCORE:"):
                try:
                    score = max(0, min(100, int(line.split(":", 1)[1].strip())))
                except ValueError:
                    pass
            elif line.startswith("REASON:"):
                reason = line.split(":", 1)[1].strip()

        logger.info(f"Gemini: {lead.get('email')} → {score} | {reason}")

    except Exception as e:
        logger.warning(f"Gemini unavailable ({e}) — using heuristic fallback")
        score = 0
        if lead.get("phone"):
            score += 25
        if lead.get("email") and "placeholder" not in lead.get("email", ""):
            score += 20
        if lead.get("address"):
            score += 15
        if lead.get("name"):
            score += 10
        if lead.get("title") or lead.get("source"):
            score += 10
        if lead.get("website"):
            score += 10
        reason = "Heuristic fallback (Gemini unavailable)"

    return {
        "score": score,
        "decision": "hot" if score >= 50 else "cold",
        "reason": reason,
    }


# ── Graph ─────────────────────────────────────────────────────────────────────
def build_graph():
    graph = StateGraph(AgentState)
    graph.add_node("enrich", enrich_with_tavily)
    graph.add_node("evaluate", score_with_gemini)  # Fixed unique node name
    graph.set_entry_point("enrich")
    graph.add_edge("enrich", "evaluate")
    graph.add_edge("evaluate", END)
    return graph.compile()


try:
    lead_scoring_graph = build_graph()
    logger.info("LangGraph scoring graph (Tavily + Gemini) initialized successfully.")
except Exception as e:
    logger.error(f"CRITICAL ERROR: LangGraph initialization failed! Error: {e}")
    logger.error(traceback.format_exc())
    lead_scoring_graph = None
