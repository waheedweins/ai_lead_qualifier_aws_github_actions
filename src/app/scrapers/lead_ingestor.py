import logging
from sqlalchemy.orm import Session
from src.app.services.lead_service import LeadService
from src.app.schemas.lead import LeadCreate
from src.app.crud.lead import get_lead_by_phone, get_lead_by_email

logger = logging.getLogger("lead-engine.scrapers.ingestor")


def _extract(item: dict, keys: list) -> str:
    """Safely extract first non-empty value from multiple possible keys."""
    for key in keys:
        val = item.get(key)
        if not val:
            continue
        if isinstance(val, list) and val:
            first = val[0]
            return str(first).strip() if first else ""
        if isinstance(val, str):
            return val.strip()
    return ""


def _is_placeholder_email(email: str) -> bool:
    """Detect auto-generated placeholder emails — don't ingest these as real leads."""
    if not email:
        return True
    lowered = email.lower()
    return any(x in lowered for x in ["placeholder", "no_email", "@placeholder", "@unknown"])


def ingest_leads(db: Session, scraped_data: list, source: str = "google_maps") -> int:
    """
    Ingest a list of raw scraped records into the database.
    Skips duplicates and placeholder-only contacts.
    
    RESTRICTION: Capped at a maximum of 2 records for testing quotas and safety limits.
    Returns count of new leads inserted.
    """
    service = LeadService(db)
    inserted = 0

    # RESTRICTION: Limit incoming scraped data to max 2 items for test mode
    scraped_data = scraped_data[:2]
    logger.info(f"Ingesting {len(scraped_data)} raw records from '{source}' (Test Mode: max 2)")

    for idx, item in enumerate(scraped_data):
        # ── Extract fields ─────────────────────────────────────────────────
        business_name = (
            item.get("title") or item.get("name") or item.get("company") or f"Lead-{idx}"
        )
        phone = _extract(item, ["phone", "phoneNumber", "internationalPhoneNumber", "phoneLocal", "phones"])
        email = _extract(item, ["email", "emails", "emailAddress"])
        address = (
            item.get("address") or item.get("fullAddress") or
            item.get("addressString") or item.get("raw_address") or ""
        )
        category = (
            item.get("categoryName") or item.get("subCategory") or
            item.get("title") or item.get("industry") or "Business"
        )
        website = item.get("website") or item.get("websiteUrl") or item.get("website_url") or ""

        # ── Skip if no real contact info ───────────────────────────────────
        # Only skip if BOTH phone and email are missing — we still want phone-only leads
        if not phone and (not email or _is_placeholder_email(email)):
            logger.debug(f"Skipping '{business_name}' — no phone or real email")
            continue

        # ── Duplicate checks ───────────────────────────────────────────────
        if phone and get_lead_by_phone(db, phone):
            logger.debug(f"Duplicate phone skipped: {phone}")
            continue

        # Build a placeholder email from phone for phone-only leads
        if not email or _is_placeholder_email(email):
            if phone:
                clean = phone.replace("+", "").replace(" ", "").replace("-", "")
                email = f"phone_{clean}@noemail.placeholder"
            else:
                continue  # nothing to save

        if get_lead_by_email(db, email):
            logger.debug(f"Duplicate email skipped: {email}")
            continue

        # ── Ingest ─────────────────────────────────────────────────────────
        try:
            lead = LeadCreate(
                name=business_name,
                email=email,
                phone=phone or None,
                source=source,
                title=category,
                address=address,
                website=website or None,
            )
            service.create(lead)
            inserted += 1
            logger.info(f"[{source}] Inserted lead #{inserted}: {business_name} | {email}")
        except Exception as e:
            logger.error(f"Failed to insert '{business_name}': {e}")
            continue

    logger.info(f"Ingestion complete: {inserted}/{len(scraped_data)} new leads from '{source}' (Test Mode)")
    return inserted
