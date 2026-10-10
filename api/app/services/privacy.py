"""Who can see which codes.

The rules:
- You always see your own codes, shared or private.
- Other vault members see your code only when it is Shared.
- Private codes count toward their owner's own sets only and never appear
  in the pooled (household) view.
"""
from sqlalchemy import and_, or_, select
from sqlalchemy.orm import Session

from app.models import Code, User, Vault, VaultMember, Visibility


def current_vault_id(db: Session, user: User, year: int) -> int | None:
    """The vault this user belongs to for the given season, if any."""
    return db.scalar(
        select(VaultMember.vault_id)
        .join(Vault, Vault.id == VaultMember.vault_id)
        .where(VaultMember.user_id == user.id, Vault.campaign_year == year)
    )


def can_view(code: Code, user: User, vault_id: int | None) -> bool:
    if code.owner_id == user.id:
        return True
    return code.visibility == Visibility.SHARED and vault_id is not None and code.vault_id == vault_id


def visible_filter(user: User, vault_id: int | None):
    """Codes list: everything of mine, plus shared codes of my vault-mates."""
    mine = Code.owner_id == user.id
    if vault_id is None:
        return mine
    return or_(mine, and_(Code.vault_id == vault_id, Code.visibility == Visibility.SHARED))


def mine_filter(user: User):
    """My own codes, shared and private. Used for my personal set progress."""
    return Code.owner_id == user.id


def pooled_filter(user: User, vault_id: int | None):
    """Household view: shared codes from every vault member. Never private codes."""
    if vault_id is None:
        return and_(Code.owner_id == user.id, Code.visibility == Visibility.SHARED)
    return and_(Code.vault_id == vault_id, Code.visibility == Visibility.SHARED)
