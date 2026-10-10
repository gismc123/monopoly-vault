from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.auth import current_user
from app.db import get_db
from app.deps import current_season
from app.models import User
from app.schemas import CodeOut, code_out
from app.season import Season
from app.services import codes as svc

router = APIRouter(prefix="/api/session", tags=["session"])


@router.post("/start", response_model=list[CodeOut])
def start(user: User = Depends(current_user), db: Session = Depends(get_db), season: Season = Depends(current_season)):
    """Called when the app opens. Returns codes copied in an earlier session that still need an answer."""
    return [code_out(c, user, season) for c in svc.start_session(db, user)]


@router.get("/pending", response_model=list[CodeOut])
def pending(user: User = Depends(current_user), db: Session = Depends(get_db), season: Season = Depends(current_season)):
    return [code_out(c, user, season) for c in svc.pending_confirmations(db, user)]
