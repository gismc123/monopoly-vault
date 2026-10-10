from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.auth import current_user
from app.db import get_db
from app.deps import current_season
from app.models import User
from app.season import Season
from app.services.codes import entries_today

router = APIRouter(prefix="/api/season", tags=["season"])


@router.get("")
def season_info(season: Season = Depends(current_season)):
    """The active season: pieces, color sets, and promo limits."""
    return {
        "year": season.year,
        "name": season.name,
        "daily_entry_limit": season.daily_entry_limit,
        "claim_deadline": season.claim_deadline.isoformat(),
        "sets": [
            {
                "id": s.id,
                "name": s.name,
                "color": s.color,
                "pieces": [{"number": p.number, "name": p.name} for p in s.pieces],
            }
            for s in season.sets
        ],
    }


@router.get("/today")
def today(
    tz: str = "UTC",
    user: User = Depends(current_user),
    db: Session = Depends(get_db),
    season: Season = Depends(current_season),
):
    """How many codes I've copied today, against McDonald's daily entry limit."""
    return {"entries_today": entries_today(db, user, tz), "daily_entry_limit": season.daily_entry_limit}
