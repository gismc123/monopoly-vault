"""Which pieces are held and when a color set is ready to redeem."""
from types import SimpleNamespace

from app.models import CodeStatus
from app.season import load_season
from app.services.collection import build_collection, ready_set_ids

SEASON = load_season(2026)


def fake_code(piece, status=CodeStatus.AVAILABLE):
    return SimpleNamespace(piece_number=piece, status=status)


def by_name(sets, name):
    return next(s for s in sets if s["name"] == name)


def test_season_has_28_pieces_in_10_sets():
    assert len(SEASON.sets) == 10
    assert sorted(SEASON.pieces) == list(range(901, 929))


def test_empty_collection_has_nothing_ready():
    sets = build_collection(SEASON, [])
    assert not any(s["complete"] for s in sets)
    assert by_name(sets, "Dark Blue")["missing"] == ["Park Place", "Boardwalk"]


def test_set_is_complete_when_every_piece_is_held():
    sets = build_collection(SEASON, [fake_code(921), fake_code(922)])
    dark_blue = by_name(sets, "Dark Blue")
    assert dark_blue["complete"]
    assert dark_blue["missing"] == []
    assert ready_set_ids(SEASON, [fake_code(921), fake_code(922)]) == {8}


def test_missing_piece_is_reported():
    red = by_name(build_collection(SEASON, [fake_code(912), fake_code(914)]), "Red")
    assert not red["complete"]
    assert red["held_count"] == 2
    assert red["missing"] == ["Indiana Avenue"]


def test_pending_still_counts_but_used_does_not():
    codes = [fake_code(921, CodeStatus.PENDING), fake_code(922, CodeStatus.USED)]
    dark_blue = by_name(build_collection(SEASON, codes), "Dark Blue")
    assert not dark_blue["complete"]
    assert dark_blue["missing"] == ["Boardwalk"]
    assert dark_blue["pieces"][1]["used"] == 1


def test_duplicates_are_counted():
    sets = build_collection(SEASON, [fake_code(927), fake_code(927), fake_code(928)])
    utilities = by_name(sets, "Utilities")
    assert utilities["pieces"][0]["available"] == 2
    assert utilities["complete"]
