import logging

from fastapi import APIRouter, Depends, UploadFile
from sqlalchemy.orm import Session

from app.auth import current_user
from app.config import get_settings
from app.db import get_db
from app.deps import current_season
from app.models import User
from app.season import Season
from app.services import ocr, photos

router = APIRouter(prefix="/api/ocr", tags=["ocr"])
log = logging.getLogger(__name__)


@router.post("")
def read_photo(image: UploadFile, user: User = Depends(current_user), season: Season = Depends(current_season)):
    """Save the original photo and suggest the code (and piece) printed on it.

    Nothing is added yet: the app shows the result so the user can confirm or
    correct it, then sends `photo_token` along with the code to POST /api/codes.
    """
    data = image.file.read(get_settings().max_upload_mb * 1024 * 1024 + 1)
    token = photos.save_upload(user, season.year, data)
    try:
        text = ocr.read_text(data, season)
    except Exception:
        log.exception("OCR failed")
        text = ""
    return {
        "photo_token": token,
        "text": text,
        "candidates": ocr.find_code_candidates(text, season),
        "piece_number": ocr.find_piece(text, season),
    }


@router.delete("/{photo_token}", status_code=204)
def discard_photo(photo_token: str, user: User = Depends(current_user), db: Session = Depends(get_db),
                  season: Season = Depends(current_season)):
    """Throw away a photo the user decided not to save (Retake or Cancel)."""
    photos.discard_upload(db, user, season.year, photo_token)
