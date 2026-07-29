import logging
from src.app.services.langgraph_engine import lead_scoring_graph
from src.app.services.outreach_graph import outreach_graph

logger = logging.getLogger("lead-engine.lead-processor")


def process_lead(lead: dict) -> dict:
    """
    Runs a single lead through:
    1. LangGraph scoring (Tavily enrichment + Gemini AI)
    2. Outreach graph if HOT (personalized WhatsApp or email via Gemini)

    Returns result dict with score, decision, reason.
    """
    if lead_scoring_graph is None:
        logger.error("LangGraph not initialized — skipping lead")
        return {"score": 0, "decision": "cold", "reason": "Engine unavailable"}

    try:
        result = lead_scoring_graph.invoke({
            "lead": lead,
            "score": 0,
            "query": "",
            "results": [],
            "decision": "",
            "reason": "",
            "website_summary": "",
        })

        decision = result.get("decision", "cold")
        score = result.get("score", 0)
        reason = result.get("reason", "")
        logger.info(f"Lead {lead.get('email')} → score={score} ({decision}): {reason}")

        if decision == "hot":
            logger.info(f"HOT lead — triggering outreach for {lead.get('email')}")
            outreach_result = outreach_graph.invoke({
                "lead": {**lead, "ai_reason": reason},
                "channel": "",
                "message": "",
                "subject": "",
            })
            result["outreach_channel"] = outreach_result.get("channel", "")
        else:
            logger.info(f"COLD lead — no outreach for {lead.get('email')}")
            result["outreach_channel"] = None

        return result

    except Exception as e:
        logger.error(f"process_lead failed for {lead.get('email')}: {e}", exc_info=True)
        raise


def process_leads_batch() -> int:
    """
    Pulls 'new' leads from DB, scores and actions them.
    
    RESTRICTION: Batch size is capped at a maximum of 2 leads for testing 
    to prevent exceeding Gemini Free tier rate limits.
    
    Updates status to 'processed' or 'failed'.
    Returns count of successfully processed leads.
    """
    from src.app.core.database import get_sessionmaker
    from src.app.models.lead import Lead
    from src.app.crud.lead import update_lead_score, mark_outreach_sent, mark_lead_failed

    SessionLocal = get_sessionmaker()
    db = SessionLocal()
    processed = 0

    try:
        new_leads = db.query(Lead).filter(Lead.status == "new").all()
        
        # RESTRICTION: Limit batch processing to max 2 leads for test mode
        new_leads = new_leads[:2]
        logger.info(f"Batch processing {len(new_leads)} new leads (Test Mode: max 2)")

        for lead_row in new_leads:
            lead_dict = {
                "id": lead_row.id,
                "name": lead_row.name,
                "email": lead_row.email,
                "phone": lead_row.phone,
                "source": lead_row.source,
                "title": lead_row.title,
                "address": lead_row.address,
                "website": lead_row.website,
            }
            try:
                result = process_lead(lead_dict)

                # Update score + reason in DB
                update_lead_score(
                    db=db,
                    lead=lead_row,
                    score=result.get("score", 0),
                    reason=result.get("reason", ""),
                )

                # Mark outreach if sent
                if result.get("decision") == "hot" and result.get("outreach_channel"):
                    mark_outreach_sent(db=db, lead=lead_row, channel=result["outreach_channel"])
                else:
                    lead_row.status = "processed"
                    db.commit()

                processed += 1

            except Exception as e:
                logger.error(f"Failed to process lead {lead_row.id}: {e}")
                mark_lead_failed(db=db, lead=lead_row)

    finally:
        db.close()

    logger.info(f"Batch complete: {processed} leads processed (Test Mode)")
    return processed
