"""Photo capture: OCR suggestions, confirm step, and the saved original photo."""
import io
import time

from PIL import Image

from app.season import load_season
from app.services import ocr, photos

SEASON = load_season(2026)


def jpeg_bytes():
    buf = io.BytesIO()
    Image.new("RGB", (64, 32), "white").save(buf, "JPEG")
    return buf.getvalue()


def test_finds_grouped_codes_and_prefers_mixed_letters_and_digits():
    text = "McDONALDS MONOPOLY\nPARK PLACE 921\nCODE: AB12 CD34 EF56\nPLAYATMCD"
    candidates = ocr.find_code_candidates(text, SEASON)
    assert candidates[0] == "AB12CD34EF56"
    assert "PLAYATMCD" in candidates  # letters-only matches are kept, but ranked lower


def test_finds_piece_by_number_or_name():
    assert ocr.find_piece("blah #921 blah", SEASON) == 921
    assert ocr.find_piece("PENNSYLVANIA RAILROAD", SEASON) == 924
    assert ocr.find_piece("nothing here 123", SEASON) is None


def test_the_need_list_is_not_mistaken_for_the_piece():
    # Real sticker text where the "#928" was misread: the NEED list must not decide it's Water Works (927).
    assert ocr.find_piece("ELECTRIC\nCOMPANY\n#92B, NEED 927/928\n$5,000$ BEST BUY TECH", SEASON) == 928
    assert ocr.find_piece("PENNSYLVANIA\nRAILROAD\nNEED 923/924/925/926", SEASON) == 924
    # Only the NEED list was read: don't guess.
    assert ocr.find_piece("D 923/924/925/926\n923/924/925/926", SEASON) is None


def test_piece_name_survives_misread_letters():
    assert ocr.find_piece("B. & O.\nRAILROA\n#925. NEED 923/924/925/926", SEASON) == 925
    assert ocr.find_piece("ANTIC AVENUE\n15, NEED 915/916/917", SEASON) == 915
    assert ocr.find_piece("ILLINOIS AVE!\n#914, NEED 912/913/914", SEASON) == 914


def test_fixes_look_alike_characters_in_printed_codes():
    # Codes are 14 characters without S, I, O, 0 or 2, so these readings can be repaired.
    text = "to collect properties*\nSXBD7KQ3HW9MRT\n*Must opt in to Rewards & register"
    assert ocr.find_code_candidates(text, SEASON)[0] == "5XBD7KQ3HW9MRT"
    assert ocr.find_code_candidates("K48) 3VQT6DMWHL", SEASON)[0] == "K48J3VQT6DMWHL"


def test_clean_readings_beat_repaired_ones():
    # The alphabet-only re-read says J; the first pass read I, which would be repaired to 1.
    text = "QHV7TBM4DIZKGL\nQHV7TBM4DIZKGL\nQHV7TBM4DJZKGL\nQHV7TBM4DJZKGL"
    assert ocr.find_code_candidates(text, SEASON)[:2] == ["QHV7TBM4DJZKGL", "QHV7TBM4D1ZKGL"]


def test_photo_upload_confirm_and_view(household, monkeypatch):
    ivan, ebony = household
    monkeypatch.setattr(ocr, "read_text", lambda data, season=None: "BOARDWALK\nZXCV 5678 BNMA")

    read = ivan.post("/api/ocr", files={"image": ("sticker.jpg", jpeg_bytes(), "image/jpeg")})
    assert read.status_code == 200, read.text
    result = read.json()
    assert result["candidates"][0] == "ZXCV5678BNMA"
    assert result["piece_number"] == 922

    # The user confirms (or corrects) and saves with the photo attached.
    saved = ivan.post("/api/codes", {"code_text": result["candidates"][0], "piece_number": 922,
                                     "photo_token": result["photo_token"]})
    code = saved.json()["code"]
    assert code["has_photo"] is True

    # Vault-mates can view the photo of a shared code; the file is the original upload.
    photo = ebony.get(f"/api/codes/{code['id']}/photo")
    assert photo.status_code == 200
    assert photo.content == jpeg_bytes()


def test_private_code_photo_is_owner_only(household, stranger, monkeypatch):
    ivan, ebony = household
    monkeypatch.setattr(ocr, "read_text", lambda data, season=None: "")
    token = ivan.post("/api/ocr", files={"image": ("s.jpg", jpeg_bytes(), "image/jpeg")}).json()["photo_token"]
    code = ivan.post("/api/codes", {"code_text": "PRIV1234", "piece_number": 901, "visibility": "private",
                                    "photo_token": token}).json()["code"]
    assert ivan.get(f"/api/codes/{code['id']}/photo").status_code == 200
    assert ebony.get(f"/api/codes/{code['id']}/photo").status_code == 404
    assert stranger.get(f"/api/codes/{code['id']}/photo").status_code == 404


def test_rejects_non_images_and_other_peoples_photo_tokens(household, monkeypatch):
    ivan, ebony = household
    monkeypatch.setattr(ocr, "read_text", lambda data, season=None: "")
    bad = ivan.post("/api/ocr", files={"image": ("notes.txt", b"hello", "text/plain")})
    assert bad.status_code == 422

    token = ivan.post("/api/ocr", files={"image": ("s.jpg", jpeg_bytes(), "image/jpeg")}).json()["photo_token"]
    stolen = ebony.post("/api/codes", {"code_text": "STEAL123", "piece_number": 901, "photo_token": token})
    assert stolen.status_code == 422
    traversal = ebony.post("/api/codes", {"code_text": "STEAL123", "piece_number": 901, "photo_token": "../x.jpg"})
    assert traversal.status_code == 422


# --- Photos from cancelled captures ---

def photo_files(tmp_root):
    return sorted(p.name for p in tmp_root.rglob("*.jpg"))


def upload(player, monkeypatch):
    monkeypatch.setattr(ocr, "read_text", lambda data, season=None: "")
    return player.post("/api/ocr", files={"image": ("s.jpg", jpeg_bytes(), "image/jpeg")}).json()["photo_token"]


def test_retake_or_cancel_deletes_the_unsaved_photo(ivan, monkeypatch):
    root = photos.root()
    token = upload(ivan, monkeypatch)
    assert photo_files(root) == [token]
    assert ivan.client.delete(f"/api/ocr/{token}", headers=ivan.headers).status_code == 204
    assert photo_files(root) == []


def test_discard_never_deletes_a_saved_photo_or_someone_elses(household, monkeypatch):
    ivan, ebony = household
    root = photos.root()
    saved = upload(ivan, monkeypatch)
    ivan.post("/api/codes", {"code_text": "SAVE1234", "piece_number": 901, "photo_token": saved})
    unsaved = upload(ivan, monkeypatch)

    ivan.client.delete(f"/api/ocr/{saved}", headers=ivan.headers)
    ebony.client.delete(f"/api/ocr/{unsaved}", headers=ebony.headers)
    assert photo_files(root) == sorted([saved, unsaved])
    assert ivan.client.delete("/api/ocr/..%2F..%2Fetc", headers=ivan.headers).status_code in (404, 422)


def test_sweep_removes_only_old_unsaved_photos(ivan, monkeypatch, db_session):
    root = photos.root()
    saved = upload(ivan, monkeypatch)
    ivan.post("/api/codes", {"code_text": "SAVE1234", "piece_number": 901, "photo_token": saved})
    abandoned = upload(ivan, monkeypatch)
    (root / "2026" / "notes.txt").write_text("not ours")  # unrelated files are left alone

    with db_session() as db:
        assert photos.sweep_unclaimed(db, max_age_hours=24) == 0  # too new
        assert photos.sweep_unclaimed(db, max_age_hours=24, now=time.time() + 25 * 3600) == 1

    assert photo_files(root) == [saved]
    assert (root / "2026" / "notes.txt").exists()
    assert abandoned not in photo_files(root)
