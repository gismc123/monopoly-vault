"""Original sticker photos, stored on disk under PHOTO_DIR.

Layout: <PHOTO_DIR>/<year>/user-<id>/<random>.<ext>
Only the relative path is saved in the database.

A photo is uploaded before its code is confirmed. If the user cancels, the app
discards it right away; anything left behind (e.g. the app was closed) is
removed by `sweep_unclaimed` once it is older than UNCLAIMED_PHOTO_HOURS.
"""
import io
import re
import time
import uuid
from pathlib import Path

from PIL import Image, UnidentifiedImageError
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import get_settings
from app.models import Code, User
from app.services.codes import AppError

EXTENSIONS = {"JPEG": "jpg", "PNG": "png", "WEBP": "webp"}
TOKEN_RE = re.compile(r"^[0-9a-f]{32}\.(jpg|png|webp)$")


def root() -> Path:
    return Path(get_settings().photo_dir)


def _user_dir(user: User, year: int) -> str:
    return f"{year}/user-{user.id}"


def save_upload(user: User, year: int, data: bytes) -> str:
    """Save an uploaded photo as-is (it is the original record) and return its token."""
    if len(data) > get_settings().max_upload_mb * 1024 * 1024:
        raise AppError(413, "That photo is too large.")
    try:
        with Image.open(io.BytesIO(data)) as img:
            fmt = img.format
            img.verify()
    except (UnidentifiedImageError, OSError):
        raise AppError(422, "That file isn't a photo we can read. Use a JPEG, PNG or WebP image.")
    if fmt not in EXTENSIONS:
        raise AppError(422, "Use a JPEG, PNG or WebP photo.")

    token = f"{uuid.uuid4().hex}.{EXTENSIONS[fmt]}"
    folder = root() / _user_dir(user, year)
    folder.mkdir(parents=True, exist_ok=True)
    (folder / token).write_bytes(data)
    return token


def claim_upload(user: User, year: int, token: str) -> str:
    """Turn an upload token into the relative path stored on the code."""
    if not TOKEN_RE.match(token):
        raise AppError(422, "Invalid photo reference.")
    relative = f"{_user_dir(user, year)}/{token}"
    if not (root() / relative).is_file():
        raise AppError(422, "The photo for this code was not found. Please take it again.")
    return relative


def absolute_path(relative: str) -> Path:
    path = (root() / relative).resolve()
    if not path.is_relative_to(root().resolve()):
        raise AppError(404, "Photo not found.")
    return path


def delete_photo(relative: str) -> None:
    try:
        absolute_path(relative).unlink(missing_ok=True)
    except AppError:
        pass


def _is_claimed(db: Session, relative: str) -> bool:
    return db.scalar(select(Code.id).where(Code.photo_path == relative)) is not None


def discard_upload(db: Session, user: User, year: int, token: str) -> None:
    """Delete an uploaded photo that was never saved with a code (Retake / Cancel)."""
    if not TOKEN_RE.match(token):
        raise AppError(422, "Invalid photo reference.")
    relative = f"{_user_dir(user, year)}/{token}"
    if not _is_claimed(db, relative):
        (root() / relative).unlink(missing_ok=True)


def sweep_unclaimed(db: Session, max_age_hours: float, now: float | None = None) -> int:
    """Delete photos older than `max_age_hours` that no code points to. Returns how many were removed.

    Only files that look like ours (<year>/user-<id>/<32 hex>.<ext>) are touched,
    so it is safe to point PHOTO_DIR at a shared NAS folder.
    """
    cutoff = (now or time.time()) - max_age_hours * 3600
    claimed = set(db.scalars(select(Code.photo_path).where(Code.photo_path.is_not(None))))
    removed = 0
    for path in root().glob("[0-9][0-9][0-9][0-9]/user-*/*"):
        if not (TOKEN_RE.match(path.name) and path.is_file()):
            continue
        relative = path.relative_to(root()).as_posix()
        if relative not in claimed and path.stat().st_mtime < cutoff:
            path.unlink(missing_ok=True)
            removed += 1
    return removed
