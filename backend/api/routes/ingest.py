# backend/api/routes/ingest.py
#
# Human-in-the-loop review surface for the card ingestion agent.
# Flow: POST /ingest/candidates {url} stages a card -> reviewer inspects
# (GET) -> approve/reject. Approved cards immediately join the live catalog
# via backend/core/card_catalog.py. All endpoints require auth.

from datetime import datetime, timezone
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from backend.auth.dependencies import get_current_user
from backend.database.connection import get_db
from backend.database.models import CardCandidate, User
from backend.integrations.card_ingest import ingest_card_from_url

router = APIRouter(prefix="/ingest", tags=["Ingest"])


# ── Models ────────────────────────────────────────────────────────────────────

class IngestRequest(BaseModel):
    url: str


class CandidateReview(BaseModel):
    note: Optional[str] = None


class CandidateResponse(BaseModel):
    id: int
    card_id: str
    source_url: str
    extractor: str
    status: str
    payload: dict
    diff: Optional[dict]
    review_note: Optional[str]

    class Config:
        from_attributes = True


# ── Routes ────────────────────────────────────────────────────────────────────

@router.post("/candidates", response_model=CandidateResponse, status_code=status.HTTP_201_CREATED)
def create_candidate(
    request: IngestRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Scrape a card page and stage the extracted card for review."""
    ok, candidate, error = ingest_card_from_url(db, request.url)
    if not ok:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=error)
    return candidate


@router.get("/candidates", response_model=List[CandidateResponse])
def list_candidates(
    status_filter: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """List ingest candidates, optionally filtered by status."""
    query = db.query(CardCandidate).order_by(CardCandidate.id.desc())
    if status_filter:
        query = query.filter(CardCandidate.status == status_filter)
    return query.all()


@router.get("/candidates/{candidate_id}", response_model=CandidateResponse)
def get_candidate(
    candidate_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    candidate = db.get(CardCandidate, candidate_id)
    if candidate is None:
        raise HTTPException(status_code=404, detail="Candidate not found")
    return candidate


@router.post("/candidates/{candidate_id}/approve", response_model=CandidateResponse)
def approve_candidate(
    candidate_id: int,
    review: CandidateReview = CandidateReview(),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Approve a pending candidate — the card joins the live catalog."""
    candidate = db.get(CardCandidate, candidate_id)
    if candidate is None:
        raise HTTPException(status_code=404, detail="Candidate not found")
    if candidate.status != "pending":
        raise HTTPException(status_code=409, detail=f"Candidate is already {candidate.status}")

    # Supersede any previously approved version of the same card
    db.query(CardCandidate).filter(
        CardCandidate.card_id == candidate.card_id,
        CardCandidate.status == "approved",
    ).update({"status": "superseded"})

    candidate.status = "approved"
    candidate.review_note = review.note
    candidate.reviewed_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(candidate)
    return candidate


@router.post("/candidates/{candidate_id}/reject", response_model=CandidateResponse)
def reject_candidate(
    candidate_id: int,
    review: CandidateReview = CandidateReview(),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    candidate = db.get(CardCandidate, candidate_id)
    if candidate is None:
        raise HTTPException(status_code=404, detail="Candidate not found")
    if candidate.status != "pending":
        raise HTTPException(status_code=409, detail=f"Candidate is already {candidate.status}")

    candidate.status = "rejected"
    candidate.review_note = review.note
    candidate.reviewed_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(candidate)
    return candidate
