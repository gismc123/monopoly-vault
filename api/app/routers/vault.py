from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.auth import current_user
from app.db import get_db
from app.deps import current_season
from app.models import User, Vault
from app.schemas import JoinIn, PersonOut, VaultIn, VaultOut
from app.season import Season
from app.services import vaults as svc

router = APIRouter(prefix="/api/vault", tags=["vault"])


def vault_out(vault: Vault) -> VaultOut:
    members = sorted(vault.members, key=lambda m: m.joined_at)
    return VaultOut(
        id=vault.id,
        name=vault.name,
        campaign_year=vault.campaign_year,
        invite_code=vault.invite_code,
        members=[PersonOut(id=m.user.id, name=m.user.name) for m in members],
    )


@router.get("", response_model=VaultOut | None)
def my_vault(user: User = Depends(current_user), db: Session = Depends(get_db), season: Season = Depends(current_season)):
    vault = svc.get_vault(db, user, season.year)
    return vault_out(vault) if vault else None


@router.post("", response_model=VaultOut, status_code=201)
def create(body: VaultIn, user: User = Depends(current_user), db: Session = Depends(get_db),
           season: Season = Depends(current_season)):
    return vault_out(svc.create_vault(db, user, season.year, body.name))


@router.post("/join", response_model=VaultOut)
def join(body: JoinIn, user: User = Depends(current_user), db: Session = Depends(get_db),
         season: Season = Depends(current_season)):
    return vault_out(svc.join_vault(db, user, season.year, body.invite_code))


@router.post("/leave", status_code=204)
def leave(user: User = Depends(current_user), db: Session = Depends(get_db), season: Season = Depends(current_season)):
    svc.leave_vault(db, user, season.year)
