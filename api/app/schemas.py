from datetime import datetime

from pydantic import BaseModel, Field

from app.models import Code, CodeStatus, User, Visibility
from app.season import Season


# --- Users and auth ---

class UserOut(BaseModel):
    id: int
    name: str
    username: str


class RegisterIn(BaseModel):
    name: str = Field(min_length=1, max_length=80)
    username: str = Field(min_length=3, max_length=40, pattern=r"^[A-Za-z0-9_.-]+$")
    password: str = Field(min_length=8, max_length=128)


class LoginIn(BaseModel):
    username: str
    password: str


class TokenOut(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserOut


def user_out(user: User) -> UserOut:
    return UserOut(id=user.id, name=user.name, username=user.username)


# --- Codes ---

class CodeIn(BaseModel):
    code_text: str = Field(min_length=1, max_length=64)
    piece_number: int
    visibility: Visibility = Visibility.SHARED
    photo_token: str | None = None  # returned by POST /api/ocr


class CodePatch(BaseModel):
    visibility: Visibility | None = None
    piece_number: int | None = None


class ConfirmIn(BaseModel):
    submitted: bool


class PersonOut(BaseModel):
    id: int
    name: str


class CodeOut(BaseModel):
    id: int
    code_text: str
    piece_number: int
    piece_name: str
    set_id: int
    owner: PersonOut
    is_mine: bool
    visibility: Visibility
    status: CodeStatus
    has_photo: bool
    collected_at: datetime
    copied_at: datetime | None
    copied_by: PersonOut | None
    confirmed_at: datetime | None
    used_by: PersonOut | None
    can_copy: bool


def _person(user: User | None) -> PersonOut | None:
    return PersonOut(id=user.id, name=user.name) if user else None


def code_out(code: Code, viewer: User, season: Season) -> CodeOut:
    piece = season.pieces.get(code.piece_number)
    return CodeOut(
        id=code.id,
        code_text=code.code_text,
        piece_number=code.piece_number,
        piece_name=piece.name if piece else f"#{code.piece_number}",
        set_id=piece.set_id if piece else 0,
        owner=_person(code.owner),
        is_mine=code.owner_id == viewer.id,
        visibility=code.visibility,
        status=code.status,
        has_photo=code.photo_path is not None,
        collected_at=code.collected_at,
        copied_at=code.copied_at,
        copied_by=_person(code.copied_by),
        confirmed_at=code.confirmed_at,
        used_by=_person(code.used_by),
        can_copy=code.status == CodeStatus.AVAILABLE
        or (code.status == CodeStatus.PENDING and code.copied_by_id == viewer.id),
    )


class CodeCreatedOut(BaseModel):
    code: CodeOut
    # Color sets that became ready to redeem because of this code.
    completed_sets: list[dict]


# --- Vaults ---

class VaultIn(BaseModel):
    name: str = Field(min_length=1, max_length=80)


class JoinIn(BaseModel):
    invite_code: str = Field(min_length=4, max_length=12)


class VaultOut(BaseModel):
    id: int
    name: str
    campaign_year: int
    invite_code: str
    members: list[PersonOut]
