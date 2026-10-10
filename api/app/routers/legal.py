from fastapi import APIRouter

from app.config import get_settings

router = APIRouter(prefix="/api/legal", tags=["legal"])


@router.get("")
def legal_info():
    """Who runs this instance, shown on the Terms of Service and Privacy Policy pages."""
    settings = get_settings()
    return {
        "operator_name": settings.operator_name.strip(),
        "operator_contact": settings.operator_contact.strip(),
        "unclaimed_photo_hours": settings.unclaimed_photo_hours,
    }
