"""Adding codes and the redemption status flow.

    Available --copy--> Pending --"yes, I submitted it"--> Used (final)
                           \\--"no, I didn't"-----------> Available

A code can only be copied while it is Available. Copying is a single atomic
UPDATE ... WHERE status = 'available', so if two people tap copy at the same
moment only one of them gets it. The person who copied it may copy it again
while it is Pending (e.g. the clipboard got lost); everyone else is blocked.
"""
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo

from sqlalchemy import func, select, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models import Code, CodeStatus, User, Visibility, utcnow
from app.season import Season, normalize_code
from app.services.privacy import can_view


class AppError(Exception):
    """An error with a message that is safe to show to the user."""

    def __init__(self, status_code: int, message: str):
        super().__init__(message)
        self.status_code = status_code
        self.message = message


def not_found() -> AppError:
    return AppError(404, "Code not found.")


def get_visible_code(db: Session, code_id: int, user: User, vault_id: int | None) -> Code:
    code = db.get(Code, code_id)
    if code is None or not can_view(code, user, vault_id):
        raise not_found()
    return code


def get_own_code(db: Session, code_id: int, user: User) -> Code:
    code = db.get(Code, code_id)
    if code is None or code.owner_id != user.id:
        raise not_found()
    return code


# --- Adding codes -----------------------------------------------------------

def create_code(
    db: Session,
    user: User,
    season: Season,
    vault_id: int | None,
    code_text: str,
    piece_number: int,
    visibility: Visibility = Visibility.SHARED,
    photo_path: str | None = None,
) -> Code:
    text = normalize_code(code_text)
    if not season.is_valid_code(text):
        raise AppError(422, "That doesn't look like a valid code. Check it and try again.")
    if piece_number not in season.pieces:
        raise AppError(422, "Pick the game piece this code came with.")

    code = Code(
        code_text=text,
        campaign_year=season.year,
        piece_number=piece_number,
        owner_id=user.id,
        vault_id=vault_id,
        visibility=visibility,
        status=CodeStatus.AVAILABLE,
        photo_path=photo_path,
    )
    db.add(code)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise AppError(409, "This code has already been added this season.")
    db.refresh(code)
    return code


# --- Status flow ------------------------------------------------------------

def copy_code(db: Session, code_id: int, user: User, vault_id: int | None, now: datetime | None = None) -> Code:
    """Claim a code for copying: Available -> Pending."""
    code = get_visible_code(db, code_id, user, vault_id)

    if code.status == CodeStatus.PENDING and code.copied_by_id == user.id:
        return code  # copying again while it's yours is fine

    claimed = db.execute(
        update(Code)
        .where(Code.id == code_id, Code.status == CodeStatus.AVAILABLE)
        .values(status=CodeStatus.PENDING, copied_at=now or utcnow(), copied_by_id=user.id)
        .execution_options(synchronize_session=False)
    ).rowcount
    db.commit()
    db.refresh(code)

    if not claimed:
        if code.status == CodeStatus.PENDING:
            who = code.copied_by.name if code.copied_by else "Someone"
            raise AppError(409, f"{who} already copied this code. It can be copied again only if they didn't submit it.")
        raise AppError(409, "This code has already been used.")
    return code


def confirm_code(db: Session, code_id: int, user: User, submitted: bool, now: datetime | None = None) -> Code:
    """Answer the next-session question. Only the person who copied it can answer."""
    code = db.get(Code, code_id)
    if code is None or code.copied_by_id != user.id or code.status != CodeStatus.PENDING:
        raise AppError(409, "This code isn't waiting for your answer.")

    if submitted:
        code.status = CodeStatus.USED
        code.confirmed_at = now or utcnow()
        code.used_by_id = user.id
    else:
        code.status = CodeStatus.AVAILABLE
        code.copied_at = None
        code.copied_by_id = None
    db.commit()
    db.refresh(code)
    return code


def start_session(db: Session, user: User, now: datetime | None = None) -> list[Code]:
    """Mark the start of a new app session and return codes to ask about."""
    user.session_started_at = now or utcnow()
    db.commit()
    return pending_confirmations(db, user)


def pending_confirmations(db: Session, user: User) -> list[Code]:
    """Codes this user copied in an earlier session that are still Pending."""
    query = select(Code).where(Code.copied_by_id == user.id, Code.status == CodeStatus.PENDING)
    if user.session_started_at is not None:
        query = query.where(Code.copied_at < user.session_started_at)
    return list(db.scalars(query.order_by(Code.copied_at)))


def entries_today(db: Session, user: User, tz_name: str, now: datetime | None = None) -> int:
    """How many codes this user copied today (in their time zone) and didn't take back."""
    try:
        tz = ZoneInfo(tz_name)
    except Exception:
        tz = timezone.utc
    local_now = (now or utcnow()).astimezone(tz)
    start_of_day = local_now.replace(hour=0, minute=0, second=0, microsecond=0)
    return db.scalar(
        select(func.count(Code.id)).where(
            Code.copied_by_id == user.id,
            Code.status.in_([CodeStatus.PENDING, CodeStatus.USED]),
            Code.copied_at >= start_of_day.astimezone(timezone.utc),
            Code.copied_at < (start_of_day + timedelta(days=1)).astimezone(timezone.utc),
        )
    ) or 0


# --- Owner edits --------------------------------------------------------------

def set_visibility(db: Session, code_id: int, user: User, visibility: Visibility) -> Code:
    code = get_own_code(db, code_id, user)
    if (
        visibility == Visibility.PRIVATE
        and code.status == CodeStatus.PENDING
        and code.copied_by_id != user.id
    ):
        raise AppError(409, "Someone in your vault is redeeming this code. Wait until they answer.")
    code.visibility = visibility
    db.commit()
    db.refresh(code)
    return code


def edit_code(
    db: Session,
    code_id: int,
    user: User,
    season: Season,
    code_text: str | None = None,
    piece_number: int | None = None,
) -> Code:
    """Fix a typo in the code or the piece it came with. Only Available codes can be changed."""
    code = get_own_code(db, code_id, user)
    if code.status != CodeStatus.AVAILABLE:
        raise AppError(409, "Only Available codes can be changed.")
    if code_text is not None:
        text = normalize_code(code_text)
        if not season.is_valid_code(text):
            raise AppError(422, "That doesn't look like a valid code. Check it and try again.")
        code.code_text = text
    if piece_number is not None:
        if piece_number not in season.pieces:
            raise AppError(422, "Unknown game piece.")
        code.piece_number = piece_number
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise AppError(409, "This code has already been added this season.")
    db.refresh(code)
    return code


def delete_code(db: Session, code_id: int, user: User) -> str | None:
    """Delete one of my Available codes. Returns its photo path so the file can be removed."""
    code = get_own_code(db, code_id, user)
    if code.status != CodeStatus.AVAILABLE:
        raise AppError(409, "Only Available codes can be deleted.")
    photo_path = code.photo_path
    db.delete(code)
    db.commit()
    return photo_path
