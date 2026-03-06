"""
TON Connect Payment Integration for Tamagochi Mini App

Endpoints for:
- Creating payment requests
- Verifying TON transactions
- Managing crypto balance
"""

from datetime import datetime, timezone
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
import hashlib
import time
import logging

from app.deps.auth import get_current_user_id
from app.deps.db import get_db
from app.models.user import User

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/v1/ton", tags=["ton"])

# ============ CONFIG ============
# Your TON wallet address to receive payments
MERCHANT_WALLET = "UQBxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"  # Replace with your TON address

# Exchange rates (update from API or set manually)
TON_TO_STARS_RATE = 100  # 1 TON = 100 Stars (example)

# Payment packages
TON_PACKAGES = [
    {"id": "ton_50", "stars": 50, "ton_amount": 0.5, "bonus": 0},
    {"id": "ton_100", "stars": 100, "ton_amount": 1.0, "bonus": 10},
    {"id": "ton_250", "stars": 250, "ton_amount": 2.5, "bonus": 30},
    {"id": "ton_500", "stars": 500, "ton_amount": 5.0, "bonus": 75},
    {"id": "ton_1000", "stars": 1000, "ton_amount": 10.0, "bonus": 200},
]


# ============ MODELS ============

class PaymentRequest(BaseModel):
    package_id: str
    wallet_address: str  # User's TON wallet


class VerifyPaymentRequest(BaseModel):
    tx_hash: str
    wallet_address: str
    expected_amount: float


# ============ HELPERS ============

async def get_or_create_user(telegram_id: int, db: AsyncSession) -> User:
    result = await db.execute(
        select(User).where(User.telegram_id == telegram_id)
    )
    user = result.scalar_one_or_none()
    if not user:
        from app.services.vpn_rewards import generate_referral_code
        user = User(telegram_id=telegram_id, referral_code=generate_referral_code())
        db.add(user)
        await db.commit()
        await db.refresh(user)
    return user


def generate_payment_id(user_id: int, package_id: str) -> str:
    """Generate unique payment ID for tracking"""
    timestamp = int(time.time())
    data = f"{user_id}:{package_id}:{timestamp}"
    return hashlib.sha256(data.encode()).hexdigest()[:16]


# ============ ENDPOINTS ============

@router.get("/config")
async def get_ton_config():
    """Get TON Connect configuration"""
    return {
        "manifest_url": "/static/tonconnect-manifest.json",
        "merchant_wallet": MERCHANT_WALLET,
        "network": "mainnet",  # or "testnet" for testing
    }


@router.get("/packages")
async def get_ton_packages():
    """Get available TON payment packages"""
    return {
        "packages": TON_PACKAGES,
        "rate": TON_TO_STARS_RATE,
        "currency": "TON",
    }


@router.post("/create-payment")
async def create_payment(
    request: PaymentRequest,
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """Create a payment request and return payment details"""
    
    # Find package
    package = next((p for p in TON_PACKAGES if p["id"] == request.package_id), None)
    if not package:
        raise HTTPException(status_code=400, detail="Invalid package ID")
    
    user = await get_or_create_user(user_id, db)
    payment_id = generate_payment_id(user_id, request.package_id)
    
    # Generate payment comment for tracking
    comment = f"tamagochi:{user_id}:{payment_id}"
    
    return {
        "payment_id": payment_id,
        "to_address": MERCHANT_WALLET,
        "amount": package["ton_amount"],
        "amount_nano": int(package["ton_amount"] * 1e9),  # Convert to nanoTON
        "comment": comment,
        "stars_to_receive": package["stars"] + package["bonus"],
        "package": package,
        # Deep link for TON wallet
        "ton_link": f"ton://transfer/{MERCHANT_WALLET}?amount={int(package['ton_amount'] * 1e9)}&text={comment}",
    }


@router.post("/verify-payment")
async def verify_payment(
    request: VerifyPaymentRequest,
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """
    Verify TON transaction and credit stars
    
    In production, you should:
    1. Use TON Center API or run your own node
    2. Verify the transaction exists and is confirmed
    3. Check the amount and recipient match
    4. Store transaction hash to prevent double-spending
    """
    
    raise HTTPException(
        status_code=501,
        detail="TON payment verification is disabled until secure on-chain validation is implemented",
    )


@router.get("/balance")
async def get_balance(
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """Get user's stars balance"""
    user = await get_or_create_user(user_id, db)
    return {
        "stars_balance": user.stars_balance or 0,
        "ton_equivalent": (user.stars_balance or 0) / TON_TO_STARS_RATE,
    }


# ============ WEBHOOK (for automatic verification) ============

@router.post("/webhook")
async def ton_webhook(
    data: dict,
    db: AsyncSession = Depends(get_db)
):
    """
    Webhook for TON transaction notifications
    
    In production, set up a service that monitors your wallet
    and sends notifications when new transactions arrive.
    
    You can use:
    - TON Center webhooks
    - Your own TON node with subscription
    - Third-party services like GetBlock
    """
    
    raise HTTPException(
        status_code=501,
        detail="TON webhook handler is disabled until signature + replay-safe verification is implemented",
    )
