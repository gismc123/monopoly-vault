import enum
from datetime import datetime, timezone

from sqlalchemy import DateTime, Enum, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class CodeStatus(str, enum.Enum):
    AVAILABLE = "available"  # collected, not yet copied
    PENDING = "pending"      # copied, outcome not confirmed yet
    USED = "used"            # confirmed submitted (final)


class Visibility(str, enum.Enum):
    SHARED = "shared"    # visible to the whole vault (default)
    PRIVATE = "private"  # visible to the owner only


def _enum(cls, name):
    # Stored as plain text with a CHECK constraint, so it is easy to read in SQL.
    return Enum(cls, name=name, native_enum=False, create_constraint=True, length=16,
                values_callable=lambda e: [m.value for m in e])


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(80))
    username: Mapped[str] = mapped_column(String(40), unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(100))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    # When the user's current app session began; codes copied before this are asked about.
    session_started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class Vault(Base):
    __tablename__ = "vaults"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(80))
    campaign_year: Mapped[int] = mapped_column(Integer, index=True)
    invite_code: Mapped[str] = mapped_column(String(12), unique=True)
    created_by_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    members: Mapped[list["VaultMember"]] = relationship(back_populates="vault", cascade="all, delete-orphan")


class VaultMember(Base):
    __tablename__ = "vault_members"

    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)
    vault_id: Mapped[int] = mapped_column(ForeignKey("vaults.id", ondelete="CASCADE"), primary_key=True)
    joined_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    vault: Mapped[Vault] = relationship(back_populates="members")
    user: Mapped[User] = relationship()


class Code(Base):
    __tablename__ = "codes"
    __table_args__ = (UniqueConstraint("campaign_year", "code_text", name="uq_codes_year_text"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    code_text: Mapped[str] = mapped_column(String(32))
    campaign_year: Mapped[int] = mapped_column(Integer, index=True)
    piece_number: Mapped[int] = mapped_column(Integer)
    owner_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    vault_id: Mapped[int | None] = mapped_column(ForeignKey("vaults.id", ondelete="SET NULL"), index=True)
    visibility: Mapped[Visibility] = mapped_column(_enum(Visibility, "visibility"), default=Visibility.SHARED)
    status: Mapped[CodeStatus] = mapped_column(_enum(CodeStatus, "code_status"), default=CodeStatus.AVAILABLE)
    photo_path: Mapped[str | None] = mapped_column(String(255))
    collected_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    copied_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    copied_by_id: Mapped[int | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"))
    confirmed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    used_by_id: Mapped[int | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"))

    owner: Mapped[User] = relationship(foreign_keys=[owner_id])
    copied_by: Mapped[User | None] = relationship(foreign_keys=[copied_by_id])
    used_by: Mapped[User | None] = relationship(foreign_keys=[used_by_id])
