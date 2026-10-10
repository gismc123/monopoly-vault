"""Set completion through the API, and ready-to-redeem alerts."""
from conftest import BALTIC, BOARDWALK, MEDITERRANEAN, PARK_PLACE


def test_adding_the_last_piece_reports_the_completed_set(ivan):
    assert ivan.add_code("PARK1111PLACE", PARK_PLACE)["completed_sets"] == []
    completed = ivan.add_code("BOARD2222WALK", BOARDWALK)["completed_sets"]
    assert {(c["name"], c["scope"]) for c in completed} == {("Dark Blue", "mine"), ("Dark Blue", "household")}


def test_household_completes_a_set_together(household):
    ivan, ebony = household
    ivan.add_code("PARK1111", PARK_PLACE)
    second = ebony.add_code("BOARD222", BOARDWALK)
    assert [(s["name"], s["scope"]) for s in second["completed_sets"]] == [("Dark Blue", "household")]
    assert ivan.collection("household")["Dark Blue"]["complete"] is True
    # Neither of them holds the whole set alone.
    assert ivan.collection("mine")["Dark Blue"]["complete"] is False


def test_private_code_alerts_only_for_the_owners_own_set(household):
    ivan, _ = household
    ivan.add_code("MEDI1111", MEDITERRANEAN)
    result = ivan.add_code("BALT2222", BALTIC, visibility="private")
    assert [(s["name"], s["scope"]) for s in result["completed_sets"]] == [("Brown", "mine")]


def test_used_codes_drop_out_of_a_ready_set(household):
    ivan, ebony = household
    park = ivan.add_code("PARK1111", PARK_PLACE)["code"]
    ebony.add_code("BOARD222", BOARDWALK)
    ivan.copy(park["id"])
    assert ivan.collection("household")["Dark Blue"]["complete"] is True  # pending still counts
    ivan.confirm(park["id"], True)
    assert ivan.collection("household")["Dark Blue"]["missing"] == ["Park Place"]
