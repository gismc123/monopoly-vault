"""Original sticker photos, stored on disk under PHOTO_DIR.

Layout: <PHOTO_DIR>/<year>/user-<id>/<random>.<ext>
Only the relative path is saved in the database.
"""
import io
import re
import uuid
from pathlib import Path

from PIL import Image, UnidentifiedImageError

from app.config import get_settings
from app.models import User
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
