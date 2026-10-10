from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.auth import create_token, current_user, hash_password, verify_password
from app.config import get_settings
from app.db import get_db
from app.models import User
from app.ratelimit import client_ip, limiter
from app.schemas import LoginIn, RegisterIn, TokenOut, UserOut, user_out

router = APIRouter(prefix="/api/auth", tags=["auth"])


@router.get("/config")
def auth_config():
    """Lets the sign-in screen know whether to offer 'Create account'."""
    return {"allow_signup": get_settings().allow_signup}


@router.post("/register", response_model=TokenOut)
def register(body: RegisterIn, request: Request, db: Session = Depends(get_db)):
    settings = get_settings()
    if not settings.allow_signup:
        raise HTTPException(403, "New sign-ups are turned off.")
    ip_key = f"signup-ip:{client_ip(request)}"
    limiter.check(ip_key, settings.signups_per_ip_per_hour, 3600)
    limiter.hit(ip_key)
    user = User(name=body.name.strip(), username=body.username.lower(), password_hash=hash_password(body.password))
    db.add(user)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(409, "That username is taken.")
    db.refresh(user)
    return TokenOut(access_token=create_token(user.id), user=user_out(user))


@router.post("/login", response_model=TokenOut)
def login(body: LoginIn, request: Request, db: Session = Depends(get_db)):
    """Too many failed attempts for one username, or from one IP address, pauses sign-in for a while."""
    settings = get_settings()
    window = settings.login_window_minutes * 60
    username = body.username.lower().strip()
    user_key, ip_key = f"login-user:{username}", f"login-ip:{client_ip(request)}"
    limiter.check(user_key, settings.login_max_failures, window)
    limiter.check(ip_key, settings.login_max_failures_per_ip, window)

    user = db.scalar(select(User).where(User.username == username))
    if user is None or not verify_password(body.password, user.password_hash):
        limiter.hit(user_key)
        limiter.hit(ip_key)
        raise HTTPException(401, "Wrong username or password.")
    limiter.clear(user_key)
    return TokenOut(access_token=create_token(user.id), user=user_out(user))


@router.get("/me", response_model=UserOut)
def me(user: User = Depends(current_user)):
    return user_out(user)
