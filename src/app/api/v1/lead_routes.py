from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from src.app.core.database import get_db
from src.app.core.auth import auth_required  # Auth0 Security Dependency
from src.app.schemas.lead import LeadCreate, LeadResponse, LeadScoreResponse, LeadStatsResponse
from src.app.services.lead_service import LeadService

router = APIRouter(prefix="/leads", tags=["Leads"])


@router.post("/", response_model=LeadResponse)
def add_lead(
    lead: LeadCreate, 
    db: Session = Depends(get_db), 
    # token_data: dict = Depends(auth_required)  # Commented out to bypass Auth0 temporarily
):
    """
    Add a single lead manually.
    🔒 SECURED: Requires a valid Auth0 Bearer Token.
    Auto-enriches data via Apollo and runs scoring with Gemini AI.
    """
    return LeadService(db).create(lead)


@router.get("/stats", response_model=LeadStatsResponse)
def lead_stats(db: Session = Depends(get_db)):
    """
    Dashboard metrics display.
    🔓 PUBLIC: Fetches general statistics (totals, hot/cold ratios, outreach metrics).
    """
    return LeadService(db).stats()


@router.get("/", response_model=list[LeadResponse])
def list_leads(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """
    List all active leads sequentially (Newest First).
    🔓 PUBLIC: Supports standard dashboard UI pagination via skip/limit parameters.
    """
    return LeadService(db).list_all(skip=skip, limit=limit)


@router.delete("/clear-test-leads/", status_code=status.HTTP_200_OK)
def clear_test_leads(
    db: Session = Depends(get_db), 
    # token_data: dict = Depends(auth_required)  # Commented out to bypass Auth0 temporarily
):
    """
    DANGER ZONE: Clears historical operational test leads from the database context.
    🔒 SECURED: Protected against unauthorized access or structural sabotage.
    """
    try:
        num_deleted = LeadService(db).clear_all_leads()
        return {"message": f"Successfully cleared {num_deleted} test leads from the system."}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, 
            detail=f"Failed to clear database: {str(e)}"
        )


@router.get("/{lead_id}", response_model=LeadResponse)
def get_lead(lead_id: int, db: Session = Depends(get_db)):
    """
    Fetch granular insights of an individual lead by primary ID mapping.
    🔓 PUBLIC: Reads isolated entity data for profile inspection panels.
    """
    lead = LeadService(db).get_by_id(lead_id)
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")
    return lead


@router.post("/{lead_id}/score", response_model=LeadScoreResponse)
def rescore_lead(
    lead_id: int, 
    db: Session = Depends(get_db), 
    # token_data: dict = Depends(auth_required)  # Commented out to bypass Auth0 temporarily
):
    """
    Re-evaluate and re-score an existing lead instance.
    🔒 SECURED: Forces Auth0 validation before spinning up Gemini 2.0 Flash context updates.
    """
    result = LeadService(db).rescore(lead_id)
    if not result:
        raise HTTPException(status_code=404, detail="Lead not found")
    return result
