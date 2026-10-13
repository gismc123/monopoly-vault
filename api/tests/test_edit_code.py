"""Fixing a code's text or piece after it was added."""
from conftest import BALTIC, BOARDWALK


def test_owner_can_fix_code_text_and_piece(ivan):
    code = ivan.add_code("AAAA1111", BALTIC)["code"]
    r = ivan.patch(f"/api/codes/{code['id']}", {"code_text": "bbbb-2222", "piece_number": BOARDWALK})
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["code_text"] == "BBBB2222"  # normalized like a new code
    assert body["piece_number"] == BOARDWALK


def test_invalid_code_text_is_rejected_and_nothing_changes(ivan):
    code = ivan.add_code("AAAA1111", BALTIC)["code"]
    r = ivan.patch(f"/api/codes/{code['id']}", {"code_text": "AB!", "piece_number": BOARDWALK})
    assert r.status_code == 422
    assert ivan.codes()[0]["code_text"] == "AAAA1111"
    assert ivan.codes()[0]["piece_number"] == BALTIC


def test_cannot_change_to_a_code_already_added(ivan):
    ivan.add_code("AAAA1111", BALTIC)
    other = ivan.add_code("BBBB2222", BALTIC)["code"]
    r = ivan.patch(f"/api/codes/{other['id']}", {"code_text": "AAAA1111"})
    assert r.status_code == 409
    assert "already been added" in r.json()["detail"]


def test_only_the_owner_can_edit(household):
    ivan, ebony = household
    code = ivan.add_code("AAAA1111", BALTIC)["code"]
    assert ebony.patch(f"/api/codes/{code['id']}", {"code_text": "BBBB2222"}).status_code == 404


def test_pending_codes_cannot_be_edited(ivan):
    code = ivan.add_code("AAAA1111", BALTIC)["code"]
    ivan.copy(code["id"])
    assert ivan.patch(f"/api/codes/{code['id']}", {"code_text": "BBBB2222"}).status_code == 409
