"""Set completion: which pieces you hold and which color sets are ready.

A piece counts as held when it has at least one Available or Pending code.
Pending codes still count so a set doesn't drop out of "ready" halfway through
redeeming it. Used codes are shown, but no longer count as held.
"""
from collections import Counter
from collections.abc import Iterable

from app.models import Code, CodeStatus
from app.season import Season


def build_collection(season: Season, codes: Iterable[Code]) -> list[dict]:
    counts: Counter[tuple[int, CodeStatus]] = Counter((c.piece_number, c.status) for c in codes)

    sets = []
    for color_set in season.sets:
        pieces = []
        for piece in color_set.pieces:
            available = counts[(piece.number, CodeStatus.AVAILABLE)]
            pending = counts[(piece.number, CodeStatus.PENDING)]
            used = counts[(piece.number, CodeStatus.USED)]
            pieces.append({
                "number": piece.number,
                "name": piece.name,
                "available": available,
                "pending": pending,
                "used": used,
                "held": available + pending > 0,
            })
        sets.append({
            "id": color_set.id,
            "name": color_set.name,
            "color": color_set.color,
            "pieces": pieces,
            "held_count": sum(p["held"] for p in pieces),
            "complete": all(p["held"] for p in pieces),
            "missing": [p["name"] for p in pieces if not p["held"]],
        })
    return sets


def ready_set_ids(season: Season, codes: Iterable[Code]) -> set[int]:
    return {s["id"] for s in build_collection(season, codes) if s["complete"]}
