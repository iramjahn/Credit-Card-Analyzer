# backend/api/routes/plaid.py
#
# Plaid integration routes — currently using mock responses.
# To go live: set PLAID_CLIENT_ID, PLAID_SECRET, PLAID_ENV env vars
# and replace mock_ helpers with real plaid-python SDK calls.

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from typing import Optional
from datetime import date

from backend.auth.dependencies import get_current_user
from backend.database.models import User

router = APIRouter(prefix="/plaid", tags=["plaid"])


# ── Request / Response models ─────────────────────────────────────────────────

class LinkTokenResponse(BaseModel):
    link_token: str
    expiration: str


class ExchangeTokenRequest(BaseModel):
    public_token: str
    institution_name: Optional[str] = None


class ExchangeTokenResponse(BaseModel):
    success: bool
    institution_name: Optional[str]
    message: str


class PlaidTransaction(BaseModel):
    transaction_id: str
    date: str
    name: str
    amount: float
    category: str


class PlaidTransactionsResponse(BaseModel):
    user_id: int
    transactions: list[PlaidTransaction]
    total: int


# ── Mock helpers ──────────────────────────────────────────────────────────────

def _mock_link_token(user_id: int) -> dict:
    return {
        "link_token": f"link-sandbox-mock-{user_id}-abc123",
        "expiration": "2026-05-01T00:00:00Z",
    }


def _mock_transactions(user_id: int) -> list[dict]:
    return [
        {"transaction_id": "tx_001", "date": str(date.today()), "name": "Whole Foods", "amount": 87.43, "category": "groceries"},
        {"transaction_id": "tx_002", "date": str(date.today()), "name": "Delta Airlines", "amount": 342.00, "category": "flights"},
        {"transaction_id": "tx_003", "date": str(date.today()), "name": "Chipotle", "amount": 14.75, "category": "dining"},
        {"transaction_id": "tx_004", "date": str(date.today()), "name": "Netflix", "amount": 15.49, "category": "streaming"},
        {"transaction_id": "tx_005", "date": str(date.today()), "name": "CVS Pharmacy", "amount": 23.10, "category": "drugstores"},
    ]


# ── Routes ────────────────────────────────────────────────────────────────────

@router.post("/create-link-token", response_model=LinkTokenResponse)
def create_link_token(current_user: User = Depends(get_current_user)):
    """Generate a Plaid Link token to initialize the Link flow."""
    data = _mock_link_token(current_user.id)
    return LinkTokenResponse(**data)


@router.post("/exchange-token", response_model=ExchangeTokenResponse)
def exchange_token(
    request: ExchangeTokenRequest,
    current_user: User = Depends(get_current_user),
):
    """Exchange a Plaid public_token for an access_token."""
    if not request.public_token:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="public_token is required")

    # TODO: replace with plaid_client.item_public_token_exchange(request.public_token)
    return ExchangeTokenResponse(
        success=True,
        institution_name=request.institution_name or "Mock Bank",
        message="Account linked successfully (mock mode)",
    )


@router.get("/transactions", response_model=PlaidTransactionsResponse)
def get_transactions(current_user: User = Depends(get_current_user)):
    """Fetch transactions for the authenticated user from Plaid."""
    # TODO: replace with real Plaid transactions_get call using stored access_token
    txs = _mock_transactions(current_user.id)
    return PlaidTransactionsResponse(
        user_id=current_user.id,
        transactions=[PlaidTransaction(**t) for t in txs],
        total=len(txs),
    )
