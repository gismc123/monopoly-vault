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
    assert ocr.find_piece("blah 921 blah", SEASON) == 921
    assert ocr.find_piece("PENNSYLVANIA RAILROAD", SEASON) == 924
    assert ocr.find_piece("nothing here 123", SEASON) is None


def test_photo_upload_confirm_and_view(household, monkeypatch):
    ivan, ebony = household
    monkeypatch.setattr(ocr, "read_text", lambda data: "BOARDWALK\nZXCV 5678 BNMA")

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
    monkeypatch.setattr(ocr, "read_text", lambda data: "")
    token = ivan.post("/api/ocr", files={"image": ("s.jpg", jpeg_bytes(), "image/jpeg")}).json()["photo_token"]
    code = ivan.post("/api/codes", {"code_text": "PRIV1234", "piece_number": 901, "visibility": "private",
                                    "photo_token": token}).json()["code"]
    assert ivan.get(f"/api/codes/{code['id']}/photo").status_code == 200
    assert ebony.get(f"/api/codes/{code['id']}/photo").status_code == 404
    assert stranger.get(f"/api/codes/{code['id']}/photo").status_code == 404


def test_rejects_non_images_and_other_peoples_photo_tokens(household, monkeypatch):
    ivan, ebony = household
    monkeypatch.setattr(ocr, "read_text", lambda data: "")
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
    monkeypatch.setattr(ocr, "read_text", lambda data: "")
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
