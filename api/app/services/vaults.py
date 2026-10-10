"""Vaults: the shared household space. One vault per person per season."""
import secrets

from sqlalchemy import select, update
from sqlalchemy.orm import Session

from app.models import Code, User, Vault, VaultMember
from app.services.codes import AppError
from app.services.privacy import current_vault_id

# No 0/O or 1/I/L, so invite codes are easy to read out loud.
INVITE_ALPHABET = "ABCDEFGHJKMNPQRSTUVWXYZ23456789"


def new_invite_code(db: Session) -> str:
    while True:
        code = "".join(secrets.choice(INVITE_ALPHABET) for _ in range(8))
        if not db.scalar(select(Vault.id).where(Vault.invite_code == code)):
            return code


def get_vault(db: Session, user: User, year: int) -> Vault | None:
    vault_id = current_vault_id(db, user, year)
    return db.get(Vault, vault_id) if vault_id else None


def _ensure_not_in_vault(db: Session, user: User, year: int) -> None:
    if current_vault_id(db, user, year):
        raise AppError(409, "You're already in a vault this season. Leave it first.")


def _join(db: Session, user: User, vault: Vault) -> Vault:
    db.add(VaultMember(user_id=user.id, vault_id=vault.id))
    # Codes added before joining become part of the vault (private ones stay private).
    db.execute(
        update(Code)
        .where(Code.owner_id == user.id, Code.campaign_year == vault.campaign_year, Code.vault_id.is_(None))
        .values(vault_id=vault.id)
    )
    db.commit()
    db.refresh(vault)
    return vault


def create_vault(db: Session, user: User, year: int, name: str) -> Vault:
    _ensure_not_in_vault(db, user, year)
    vault = Vault(name=name.strip(), campaign_year=year, invite_code=new_invite_code(db), created_by_id=user.id)
    db.add(vault)
    db.flush()
    return _join(db, user, vault)


def join_vault(db: Session, user: User, year: int, invite_code: str) -> Vault:
    _ensure_not_in_vault(db, user, year)
    code = invite_code.strip().upper().replace(" ", "").replace("-", "")
    vault = db.scalar(select(Vault).where(Vault.invite_code == code, Vault.campaign_year == year))
    if vault is None:
        raise AppError(404, "No vault found with that invite code.")
    return _join(db, user, vault)


def leave_vault(db: Session, user: User, year: int) -> None:
    vault = get_vault(db, user, year)
    if vault is None:
        raise AppError(409, "You're not in a vault.")
    db.execute(update(Code).where(Code.owner_id == user.id, Code.vault_id == vault.id).values(vault_id=None))
    membership = db.get(VaultMember, (user.id, vault.id))
    db.delete(membership)
    db.flush()
    db.refresh(vault)
    if not vault.members:
        db.delete(vault)
    db.commit()
