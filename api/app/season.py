"""Loads the yearly season file (pieces, winning combinations and promo limits).

Each October campaign is its own season. To set up next year, add
`seasons/<year>.json` with the same shape and set CAMPAIGN_YEAR in .env.
"""
import json
import re
from dataclasses import dataclass
from datetime import date
from functools import lru_cache
from pathlib import Path

SEASONS_DIR = Path(__file__).parent / "seasons"


@dataclass(frozen=True)
class Piece:
    number: int
    name: str
    set_id: int


@dataclass(frozen=True)
class ColorSet:
    id: int
    name: str
    color: str
    pieces: tuple[Piece, ...]


@dataclass(frozen=True)
class Season:
    year: int
    name: str
    daily_entry_limit: int
    claim_deadline: date
    code_pattern: str
    sets: tuple[ColorSet, ...]
    # How printed codes look, so OCR can fix look-alike misreads (S->5, O->Q). Not enforced on save.
    code_length: int | None = None
    code_alphabet: str | None = None

    @property
    def pieces(self) -> dict[int, Piece]:
        return {p.number: p for s in self.sets for p in s.pieces}

    def set_by_id(self, set_id: int) -> ColorSet:
        return next(s for s in self.sets if s.id == set_id)

    def is_valid_code(self, code_text: str) -> bool:
        return re.fullmatch(self.code_pattern, code_text) is not None


def normalize_code(text: str) -> str:
    """Codes are stored upper-case with spaces and dashes removed."""
    return re.sub(r"[\s\-]", "", text).upper()


@lru_cache
def load_season(year: int) -> Season:
    path = SEASONS_DIR / f"{year}.json"
    if not path.exists():
        raise RuntimeError(f"No season file for {year}. Expected {path}.")
    data = json.loads(path.read_text())
    sets = tuple(
        ColorSet(
            id=s["id"],
            name=s["name"],
            color=s["color"],
            pieces=tuple(Piece(number=p["number"], name=p["name"], set_id=s["id"]) for p in s["pieces"]),
        )
        for s in data["sets"]
    )
    return Season(
        year=data["year"],
        name=data["name"],
        daily_entry_limit=data["daily_entry_limit"],
        claim_deadline=date.fromisoformat(data["claim_deadline"]),
        code_pattern=data["code_pattern"],
        sets=sets,
        code_length=data.get("code_length"),
        code_alphabet=data.get("code_alphabet"),
    )
