from typing import Literal

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.auth import current_user
from app.db import get_db
from app.deps import current_season
from app.models import Code, User
from app.season import Season
from app.services.collection import build_collection
from app.services.privacy import current_vault_id, mine_filter, pooled_filter

router = APIRouter(prefix="/api/collection", tags=["collection"])


@router.get("")
def collection(
    scope: Literal["household", "mine"] = "household",
    user: User = Depends(current_user),
    db: Session = Depends(get_db),
    season: Season = Depends(current_season),
):
    """Progress by color set and piece. 'household' = shared codes of the whole vault; 'mine' = all my codes."""
    vault_id = current_vault_id(db, user, season.year)
    where = pooled_filter(user, vault_id) if scope == "household" else mine_filter(user)
    codes = db.scalars(select(Code).where(Code.campaign_year == season.year, where)).all()
    sets = build_collection(season, codes)
    return {"scope": scope, "has_vault": vault_id is not None, "sets": sets}
