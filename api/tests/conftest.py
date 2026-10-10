"""Test setup: an in-memory SQLite database and a temp photo folder per test."""
import os

os.environ.update(DATABASE_URL="sqlite://", JWT_SECRET="test-secret", CAMPAIGN_YEAR="2026", ALLOW_SIGNUP="true")

import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402
from sqlalchemy import create_engine  # noqa: E402
from sqlalchemy.orm import sessionmaker  # noqa: E402
from sqlalchemy.pool import StaticPool  # noqa: E402

from app import models  # noqa: E402,F401
from app.config import get_settings  # noqa: E402
from app.db import Base, get_db  # noqa: E402
from app.main import app  # noqa: E402

# Piece numbers from the 2026 season file, used throughout the tests.
BALTIC, MEDITERRANEAN = 902, 901
PARK_PLACE, BOARDWALK = 921, 922


@pytest.fixture
def db_session(tmp_path, monkeypatch):
    monkeypatch.setenv("PHOTO_DIR", str(tmp_path / "photos"))
    get_settings.cache_clear()
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)
    yield Session
    engine.dispose()
    get_settings.cache_clear()


@pytest.fixture
def client(db_session):
    def override_db():
        db = db_session()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


class Player:
    """A signed-in test user with helpers for the API calls the tests make."""

    def __init__(self, client: TestClient, username: str):
        self.client = client
        r = client.post("/api/auth/register", json={"name": username.title(), "username": username, "password": "password123"})
        assert r.status_code == 200, r.text
        self.id = r.json()["user"]["id"]
        self.headers = {"Authorization": f"Bearer {r.json()['access_token']}"}

    def get(self, url, **kw):
        return self.client.get(url, headers=self.headers, **kw)

    def post(self, url, json=None, **kw):
        return self.client.post(url, json=json, headers=self.headers, **kw)

    def patch(self, url, json=None):
        return self.client.patch(url, json=json, headers=self.headers)

    def add_code(self, code_text, piece, visibility="shared"):
        r = self.post("/api/codes", {"code_text": code_text, "piece_number": piece, "visibility": visibility})
        assert r.status_code == 201, r.text
        return r.json()

    def copy(self, code_id):
        return self.post(f"/api/codes/{code_id}/copy")

    def confirm(self, code_id, submitted):
        return self.post(f"/api/codes/{code_id}/confirm", {"submitted": submitted})

    def codes(self, scope="all"):
        return self.get("/api/codes", params={"scope": scope}).json()

    def collection(self, scope):
        return {s["name"]: s for s in self.get("/api/collection", params={"scope": scope}).json()["sets"]}


@pytest.fixture
def ivan(client):
    return Player(client, "ivan")


@pytest.fixture
def ebony(client):
    return Player(client, "ebony")


@pytest.fixture
def stranger(client):
    return Player(client, "stranger")


@pytest.fixture
def household(ivan, ebony, db_session):
    """Ivan and Ebony share a vault for the 2026 season."""
    from app.models import Vault, VaultMember

    with db_session() as db:
        vault = Vault(name="Santos", campaign_year=2026, invite_code="TESTCODE", created_by_id=ivan.id)
        db.add(vault)
        db.flush()
        db.add_all([VaultMember(user_id=ivan.id, vault_id=vault.id), VaultMember(user_id=ebony.id, vault_id=vault.id)])
        db.commit()
    return ivan, ebony
