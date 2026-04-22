# backend/api/models.py

from pydantic import BaseModel, EmailStr
from typing import Dict, List, Optional

# ============================================
# User Models
# ============================================

class UserSignup(BaseModel):
    """Request model for user signup"""
    email: EmailStr
    password: str
    first_name: Optional[str] = None
    last_name: Optional[str] = None

class UserLogin(BaseModel):
    """Request model for user login"""
    email: EmailStr
    password: str

class UserResponse(BaseModel):
    """Response model for user data"""
    id: int
    email: str
    first_name: Optional[str]
    last_name: Optional[str]

class TokenResponse(BaseModel):
    """Response model for authentication token"""
    token: str
    user: UserResponse

# ============================================
# Card Models
# ============================================

class CardRecommendationRequest(BaseModel):
    """Request for card recommendation"""
    amount: float
    category: str

class CardRecommendationResponse(BaseModel):
    """Response with card recommendation"""
    card_id: str
    card_name: str
    reward_rate: float
    points_earned: int
    cash_value: float

class CustomCardCreate(BaseModel):
    """Request to create custom card"""
    name: str
    issuer: str
    annual_fee: int
    point_value: float
    rewards: Dict[str, float]
    benefits: List[str]

class CustomCardFromURL(BaseModel):
    """Request to create card from URL"""
    url: str

class CardResponse(BaseModel):
    """Response with card data"""
    id: str
    name: str
    issuer: str
    annual_fee: int
    point_value: float
    rewards: Dict[str, float]
    benefits: List[str]

# ============================================
# Transaction Models
# ============================================

class TransactionCreate(BaseModel):
    """Request to create transaction"""
    card_id: Optional[str] = None
    amount: float
    category: str
    merchant_name: Optional[str] = None
    notes: Optional[str] = None

class TransactionResponse(BaseModel):
    """Response with transaction data"""
    id: int
    card_id: Optional[str]
    amount: float
    category: str
    merchant_name: Optional[str]
    transaction_date: str
    notes: Optional[str]

# ============================================
# Benefit Models
# ============================================

class BenefitUsageUpdate(BaseModel):
    """Request to update benefit usage"""
    card_id: str
    benefit_name: str
    amount_used: float

class BenefitResponse(BaseModel):
    """Response with benefit data"""
    card_id: str
    card_name: str
    benefit_name: str
    total_value: float
    used_value: float
    remaining_value: float
    reset_period: str
    days_until_reset: Optional[int]