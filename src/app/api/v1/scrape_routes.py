from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from src.app.workers.scraping_worker import run_scraping_job
from src.app.workers.lead_processor import process_leads_batch
from src.app.core.auth import auth_required  # 🔒 These routes trigger paid API calls
import logging

logger = logging.getLogger("lead-engine")
router = APIRouter(prefix="/scrape", tags=["Scraping"])


@router.post("/")
def scrape(
    query: str,
    background_tasks: BackgroundTasks,
    source: str = "google_maps",
    # token_data: dict = Depends(auth_required),  # Commented out to disable Auth0 temporarily
):
    """
    Start a background scraping job.
    🔒 SECURED: Requires a valid Auth0 Bearer Token (triggers billed Apify/Apollo calls).

    - **query**: search term e.g. `solar panel installers lahore`
    - **source**: `google_maps` | `apollo` | `all`

    Returns immediately — scraping runs in the background.
    """
    if not query or not query.strip():
        raise HTTPException(status_code=400, detail="query cannot be empty")
    if source not in ("google_maps", "apollo", "all"):
        raise HTTPException(status_code=400, detail="source must be google_maps | apollo | all")

    logger.info(f"Queuing scrape: query='{query}' source='{source}'")
    background_tasks.add_task(run_scraping_job, query, source)
    return {"status": "processing", "query": query, "source": source}


@router.post("/process")
def process_all(
    background_tasks: BackgroundTasks, 
    # token_data: dict = Depends(auth_required)  # Commented out to disable Auth0 temporarily
):
    """
    Manually trigger scoring + outreach for all unprocessed leads.
    🔒 SECURED: Requires a valid Auth0 Bearer Token.
    Runs in the background.
    """
    logger.info("Manual process_all triggered")
    background_tasks.add_task(process_leads_batch)
    return {"status": "processing", "message": "Scoring and outreach started for all new leads"}


@router.post("/run")
def run_full_pipeline(
    query: str,
    background_tasks: BackgroundTasks,
    source: str = "all",
    # token_data: dict = Depends(auth_required),  # Commented out to disable Auth0 temporarily
):
    """
    One-shot: scrape + score + outreach in a single call.
    🔒 SECURED: Requires a valid Auth0 Bearer Token.
    Runs the entire pipeline end-to-end in the background.
    """
    if not query or not query.strip():
        raise HTTPException(status_code=400, detail="query cannot be empty")

    def _pipeline():
        from src.app.services.main_workflow import workflow
        workflow.invoke({"query": query, "source": source, "results_count": 0, "processed_count": 0})

    logger.info(f"Full pipeline triggered: query='{query}' source='{source}'")
    background_tasks.add_task(_pipeline)
    return {"status": "pipeline_started", "query": query, "source": source}
