"""Available -> Pending -> Used, and Pending -> Available."""
from conftest import BALTIC, BOARDWALK, PARK_PLACE


def test_new_code_is_available_and_shared(ivan):
    code = ivan.add_code("abcd 1234 efgh", BALTIC)["code"]
    assert code["status"] == "available"
    assert code["visibility"] == "shared"
    assert code["code_text"] == "ABCD1234EFGH"  # normalized
    assert code["copied_at"] is None


def test_copy_moves_code_to_pending(ivan):
    code = ivan.add_code("AAAA1111", BALTIC)["code"]
    r = ivan.copy(code["id"])
    assert r.status_code == 200
    body = r.json()
    assert body["status"] == "pending"
    assert body["copied_at"] is not None
    assert body["copied_by"]["id"] == ivan.id


def test_copier_can_copy_again_while_pending(ivan):
    code = ivan.add_code("AAAA1111", BALTIC)["code"]
    first = ivan.copy(code["id"]).json()
    again = ivan.copy(code["id"])
    assert again.status_code == 200
    assert again.json()["copied_at"] == first["copied_at"]


def test_nobody_else_can_copy_a_pending_code(household):
    ivan, ebony = household
    code = ivan.add_code("AAAA1111", PARK_PLACE)["code"]
    assert ivan.copy(code["id"]).status_code == 200

    blocked = ebony.copy(code["id"])
    assert blocked.status_code == 409
    assert "Ivan already copied" in blocked.json()["detail"]
    assert ebony.codes()[0]["can_copy"] is False


def test_answering_yes_marks_used_with_timestamp(household):
    ivan, ebony = household
    code = ivan.add_code("AAAA1111", PARK_PLACE)["code"]
    ebony.copy(code["id"])

    used = ebony.confirm(code["id"], True).json()
    assert used["status"] == "used"
    assert used["confirmed_at"] is not None
    assert used["used_by"]["id"] == ebony.id

    # Used is final: it can't be copied or answered again.
    assert ivan.copy(code["id"]).status_code == 409
    assert ebony.copy(code["id"]).status_code == 409
    assert ebony.confirm(code["id"], False).status_code == 409


def test_answering_no_returns_code_to_available(household):
    ivan, ebony = household
    code = ivan.add_code("AAAA1111", BOARDWALK)["code"]
    ivan.copy(code["id"])

    back = ivan.confirm(code["id"], False).json()
    assert back["status"] == "available"
    assert back["copied_at"] is None
    assert back["copied_by"] is None

    # Now someone else may copy it.
    assert ebony.copy(code["id"]).json()["status"] == "pending"


def test_only_the_copier_can_answer(household):
    ivan, ebony = household
    code = ivan.add_code("AAAA1111", BOARDWALK)["code"]
    ebony.copy(code["id"])
    assert ivan.confirm(code["id"], True).status_code == 409
    assert ivan.codes()[0]["status"] == "pending"


def test_next_session_asks_about_codes_copied_earlier(ivan):
    code = ivan.add_code("AAAA1111", BALTIC)["code"]
    ivan.post("/api/session/start")
    ivan.copy(code["id"])

    # Same session: no question yet.
    assert ivan.get("/api/session/pending").json() == []

    # Next session: asked once, and it stays until answered.
    asked = ivan.post("/api/session/start").json()
    assert [c["id"] for c in asked] == [code["id"]]
    assert [c["id"] for c in ivan.post("/api/session/start").json()] == [code["id"]]

    ivan.confirm(code["id"], True)
    assert ivan.post("/api/session/start").json() == []


def test_entries_today_counts_copies_not_taken_back(ivan):
    a = ivan.add_code("AAAA1111", BALTIC)["code"]
    b = ivan.add_code("BBBB2222", BALTIC)["code"]
    ivan.copy(a["id"])
    ivan.copy(b["id"])
    ivan.confirm(b["id"], False)
    today = ivan.get("/api/season/today", params={"tz": "America/Chicago"}).json()
    assert today == {"entries_today": 1, "daily_entry_limit": 8}


def test_duplicate_and_invalid_codes_are_rejected(ivan, ebony):
    ivan.add_code("AAAA1111", BALTIC)
    dup = ebony.post("/api/codes", {"code_text": "aaaa-1111", "piece_number": BALTIC})
    assert dup.status_code == 409
    bad = ivan.post("/api/codes", {"code_text": "abc", "piece_number": BALTIC})
    assert bad.status_code == 422
    unknown_piece = ivan.post("/api/codes", {"code_text": "CCCC3333", "piece_number": 999})
    assert unknown_piece.status_code == 422
