"""Shared FastAPI dependencies."""
from app.config import get_settings
from app.season import Season, load_season


def current_season() -> Season:
    return load_season(get_settings().campaign_year)
