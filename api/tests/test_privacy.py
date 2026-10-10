"""Shared by default; private codes are the owner's alone."""
from conftest import BALTIC, BOARDWALK, MEDITERRANEAN, PARK_PLACE


def test_vault_mates_see_shared_but_not_private_codes(household):
    ivan, ebony = household
    ivan.add_code("SHARED11", BALTIC)
    secret = ivan.add_code("PRIVATE1", PARK_PLACE, visibility="private")["code"]

    assert {c["code_text"] for c in ivan.codes()} == {"SHARED11", "PRIVATE1"}
    assert [c["code_text"] for c in ebony.codes()] == ["SHARED11"]
    # Ebony can't copy what she can't see.
    assert ebony.copy(secret["id"]).status_code == 404


def test_people_outside_the_vault_see_nothing(household, stranger):
    ivan, _ = household
    code = ivan.add_code("SHARED11", BALTIC)["code"]
    assert stranger.codes() == []
    assert stranger.copy(code["id"]).status_code == 404


def test_private_codes_never_appear_in_the_pooled_view(household):
    ivan, ebony = household
    ivan.add_code("PRIVATE1", BALTIC, visibility="private")
    for player in (ivan, ebony):
        brown = player.collection("household")["Brown"]
        baltic = next(p for p in brown["pieces"] if p["number"] == BALTIC)
        assert baltic["held"] is False


def test_private_codes_count_toward_the_owners_own_sets(household):
    ivan, _ = household
    ivan.add_code("PRIVATE1", BALTIC, visibility="private")
    ivan.add_code("SHARED11", MEDITERRANEAN)
    assert ivan.collection("mine")["Brown"]["complete"] is True
    assert ivan.collection("household")["Brown"]["complete"] is False


def test_only_the_owner_can_change_visibility(household):
    ivan, ebony = household
    code = ivan.add_code("SHARED11", BOARDWALK)["code"]
    assert ebony.patch(f"/api/codes/{code['id']}", {"visibility": "private"}).status_code == 404
    r = ivan.patch(f"/api/codes/{code['id']}", {"visibility": "private"})
    assert r.json()["visibility"] == "private"
    assert ebony.codes() == []


def test_cannot_hide_a_code_a_vault_mate_is_redeeming(household):
    ivan, ebony = household
    code = ivan.add_code("SHARED11", BOARDWALK)["code"]
    ebony.copy(code["id"])
    assert ivan.patch(f"/api/codes/{code['id']}", {"visibility": "private"}).status_code == 409
