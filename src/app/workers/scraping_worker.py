import logging
from src.app.core.logging import logger
from src.app.core.database import get_sessionmaker
from src.app.scrapers.google_maps import GoogleMapsScraper
from src.app.scrapers.apollo_scraper import ApolloScraper
from src.app.scrapers.lead_ingestor import ingest_leads


def run_scraping_job(query: str, source: str = "google_maps") -> int:
    """
    Runs a scraping job for the given query.
    Source can be:
      - "google_maps"  — Apify Google Maps (local businesses)
      - "apollo"       — Apollo.io company search (B2B contacts)
      - "all"          — both sources combined

    RESTRICTION: Google Maps results are capped at a maximum of 2 records for testing.
    Returns total new leads inserted.
    """
    logger.info(f"Scraping job started: query='{query}' source='{source}'")

    SessionLocal = get_sessionmaker()
    db = SessionLocal()
    total_inserted = 0

    try:
        if source in ("google_maps", "all"):
            scraper = GoogleMapsScraper()
            data = scraper.scrape(search_query=query, max_results=30)
            if data:
                # RESTRICTION: Limit Google Maps scraped data to max 2 items for test mode
                data = data[:2]
                inserted = ingest_leads(db=db, scraped_data=data, source="google_maps")
                total_inserted += inserted
                logger.info(f"Google Maps: {inserted} new leads for '{query}' (Test Mode: max 2)")

        if source in ("apollo", "all"):
            apollo = ApolloScraper()
            if apollo.enabled:
                # Parse "industry location" from query e.g. "solar panel installers lahore"
                parts = query.rsplit(" ", 1)
                industry = parts[0] if len(parts) > 1 else query
                location = parts[1] if len(parts) > 1 else "Pakistan"

                # Apollo scraper already enforces a max 2 limit internally for tests
                data = apollo.search_companies(industry=industry, location=location, limit=20)
                if data:
                    inserted = ingest_leads(db=db, scraped_data=data, source="apollo")
                    total_inserted += inserted
                    logger.info(f"Apollo: {inserted} new leads for '{query}' (Test Mode: max 2)")
            else:
                logger.info("Apollo skipped — APOLLO_API_KEY not configured")

        logger.info(f"Scraping job complete: {total_inserted} total new leads for '{query}'")
        return total_inserted

    except Exception as e:
        logger.error(f"Scraping job crashed for '{query}': {e}", exc_info=True)
        raise
    finally:
        db.close()
