"""Creating, joining and leaving a vault."""
from conftest import BALTIC, BOARDWALK, PARK_PLACE


def test_create_and_join_with_invite_code(ivan, ebony):
    created = ivan.post("/api/vault", {"name": "Santos"})
    assert created.status_code == 201
    invite = created.json()["invite_code"]

    joined = ebony.post("/api/vault/join", {"invite_code": invite.lower()}).json()
    assert [m["name"] for m in joined["members"]] == ["Ivan", "Ebony"]
    assert ebony.get("/api/vault").json()["id"] == created.json()["id"]


def test_wrong_invite_code_is_rejected(ebony):
    assert ebony.post("/api/vault/join", {"invite_code": "NOPE1234"}).status_code == 404


def test_one_vault_per_season(household, stranger):
    ivan, _ = household
    assert ivan.post("/api/vault", {"name": "Second"}).status_code == 409
    other = stranger.post("/api/vault", {"name": "Other"}).json()
    assert ivan.post("/api/vault/join", {"invite_code": other["invite_code"]}).status_code == 409


def test_codes_added_before_joining_are_pooled(ivan, ebony):
    ivan.add_code("EARLY111", PARK_PLACE)
    ebony.add_code("EARLY222", BOARDWALK)
    ebony.add_code("SECRET33", BALTIC, visibility="private")

    vault = ivan.post("/api/vault", {"name": "Santos"}).json()
    ebony.post("/api/vault/join", {"invite_code": vault["invite_code"]})

    assert {c["code_text"] for c in ivan.codes()} == {"EARLY111", "EARLY222"}
    assert ivan.collection("household")["Dark Blue"]["complete"] is True


def test_leaving_takes_your_codes_out_of_the_pool(household):
    ivan, ebony = household
    ebony.add_code("EBONY111", BOARDWALK)
    assert len(ivan.codes()) == 1

    assert ebony.post("/api/vault/leave").status_code == 204
    assert ivan.codes() == []
    assert ebony.get("/api/vault").json() is None
    assert [m["name"] for m in ivan.get("/api/vault").json()["members"]] == ["Ivan"]
    # Ebony still has her own code.
    assert [c["code_text"] for c in ebony.codes()] == ["EBONY111"]
