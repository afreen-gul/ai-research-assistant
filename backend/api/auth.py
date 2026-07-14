"""Auth endpoints."""

import logging

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from api.schemas import AuthRequest, AuthResponse
from database.models import get_db
from memory.auth import authenticate_user, create_token, get_or_create_guest_user, register_user

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/auth", tags=["auth"])


@router.post("/register", response_model=AuthResponse)
async def register(body: AuthRequest, db: AsyncSession = Depends(get_db)):
    try:
        user = await register_user(db, body.username, body.password)
        token = create_token(user.id, user.username)
        return AuthResponse(token=token, user_id=user.id, username=user.username)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/login", response_model=AuthResponse)
async def login(body: AuthRequest, db: AsyncSession = Depends(get_db)):
    user = await authenticate_user(db, body.username, body.password)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    token = create_token(user.id, user.username)
    return AuthResponse(token=token, user_id=user.id, username=user.username)


@router.post("/guest", response_model=AuthResponse)
async def guest_login(db: AsyncSession = Depends(get_db)):
    user = await get_or_create_guest_user(db)
    token = create_token(user.id, user.username)
    return AuthResponse(token=token, user_id=user.id, username=user.username)
