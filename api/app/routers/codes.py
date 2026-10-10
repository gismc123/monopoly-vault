from typing import Literal

from fastapi import APIRouter, Depends
from fastapi.responses import FileResponse
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.auth import current_user
from app.db import get_db
from app.deps import current_season
from app.models import Code, CodeStatus, User, Visibility
from app.schemas import CodeCreatedOut, CodeIn, CodeOut, CodePatch, ConfirmIn, code_out
from app.season import Season
from app.services import codes as svc
from app.services import photos
from app.services.collection import ready_set_ids
from app.services.privacy import current_vault_id, mine_filter, pooled_filter, visible_filter

router = APIRouter(prefix="/api/codes", tags=["codes"])


@router.get("", response_model=list[CodeOut])
def list_codes(
    scope: Literal["all", "mine"] = "all",
    status: CodeStatus | None = None,
    user: User = Depends(current_user),
    db: Session = Depends(get_db),
    season: Season = Depends(current_season),
):
    """'all' = my codes plus my vault-mates' shared codes; 'mine' = only mine."""
    vault_id = current_vault_id(db, user, season.year)
    where = visible_filter(user, vault_id) if scope == "all" else mine_filter(user)
    query = select(Code).where(Code.campaign_year == season.year, where)
    if status:
        query = query.where(Code.status == status)
    codes = db.scalars(query.order_by(Code.piece_number, Code.collected_at)).all()
    return [code_out(c, user, season) for c in codes]


def _ready_sets(db: Session, season: Season, where) -> set[int]:
    codes = db.scalars(select(Code).where(Code.campaign_year == season.year, where)).all()
    return ready_set_ids(season, codes)


@router.post("", response_model=CodeCreatedOut, status_code=201)
def add_code(
    body: CodeIn,
    user: User = Depends(current_user),
    db: Session = Depends(get_db),
    season: Season = Depends(current_season),
):
    vault_id = current_vault_id(db, user, season.year)
    photo_path = photos.claim_upload(user, season.year, body.photo_token) if body.photo_token else None

    scopes = {"mine": mine_filter(user), "household": pooled_filter(user, vault_id)}
    before = {name: _ready_sets(db, season, where) for name, where in scopes.items()}

    code = svc.create_code(db, user, season, vault_id, body.code_text, body.piece_number, body.visibility, photo_path)

    completed = []
    for name, where in scopes.items():
        for set_id in sorted(_ready_sets(db, season, where) - before[name]):
            color_set = season.set_by_id(set_id)
            completed.append({"id": set_id, "name": color_set.name, "color": color_set.color, "scope": name})
    return CodeCreatedOut(code=code_out(code, user, season), completed_sets=completed)


@router.post("/{code_id}/copy", response_model=CodeOut)
def copy(code_id: int, user: User = Depends(current_user), db: Session = Depends(get_db),
         season: Season = Depends(current_season)):
    """Claim a code before copying it: Available -> Pending."""
    vault_id = current_vault_id(db, user, season.year)
    return code_out(svc.copy_code(db, code_id, user, vault_id), user, season)


@router.post("/{code_id}/confirm", response_model=CodeOut)
def confirm(code_id: int, body: ConfirmIn, user: User = Depends(current_user), db: Session = Depends(get_db),
            season: Season = Depends(current_season)):
    """Answer 'Did you submit it?': yes -> Used, no -> Available."""
    return code_out(svc.confirm_code(db, code_id, user, body.submitted), user, season)


@router.patch("/{code_id}", response_model=CodeOut)
def edit(code_id: int, body: CodePatch, user: User = Depends(current_user), db: Session = Depends(get_db),
         season: Season = Depends(current_season)):
    code = None
    if body.visibility is not None:
        code = svc.set_visibility(db, code_id, user, Visibility(body.visibility))
    if body.piece_number is not None:
        code = svc.set_piece(db, code_id, user, season, body.piece_number)
    if code is None:
        code = svc.get_own_code(db, code_id, user)
    return code_out(code, user, season)


@router.delete("/{code_id}", status_code=204)
def delete(code_id: int, user: User = Depends(current_user), db: Session = Depends(get_db)):
    photo_path = svc.delete_code(db, code_id, user)
    if photo_path:
        photos.delete_photo(photo_path)


@router.get("/{code_id}/photo")
def photo(code_id: int, user: User = Depends(current_user), db: Session = Depends(get_db),
          season: Season = Depends(current_season)):
    """The original sticker photo, for anyone who can see the code."""
    vault_id = current_vault_id(db, user, season.year)
    code = svc.get_visible_code(db, code_id, user, vault_id)
    path = photos.absolute_path(code.photo_path) if code.photo_path else None
    if path is None or not path.is_file():
        raise svc.AppError(404, "No photo for this code.")
    return FileResponse(path, headers={"Cache-Control": "private, max-age=86400"})
