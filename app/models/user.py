# ==============================================================
# app/models/user.py
#
# WHAT THIS FILE DOES:
#   Defines the "users" table in PostgreSQL.
#   Every attribute with a Column() becomes a column in the table.
# ==============================================================

from datetime import datetime, timezone

from sqlalchemy import Boolean, DateTime, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.database import Base


class User(Base):
    """
    CONCEPT — SQLAlchemy Declarative Model:
    By inheriting from Base, this class is registered with
    SQLAlchemy. The __tablename__ attribute tells SQLAlchemy
    what to name the table in PostgreSQL.

    CONCEPT — Mapped[] and mapped_column():
    This is the modern SQLAlchemy 2.0 syntax.
    `Mapped[str]` tells Python (and SQLAlchemy) the Python type.
    `mapped_column(String(255))` tells PostgreSQL the column type.
    They work together to give you full type safety.
    """

    __tablename__ = "users"

    # Primary key — every table must have one.
    # autoincrement=True means PostgreSQL assigns the ID automatically.
    # Mapped[int] — this column holds integers.
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    # String(255) = VARCHAR(255) in SQL — a text column with max 255 characters.
    # unique=True means no two users can have the same email.
    # index=True creates a database index on this column,
    # making lookups by email very fast.
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)

    # The full name of the user. Optional (nullable=True).
    full_name: Mapped[str] = mapped_column(String(255), nullable=True)

    # The bcrypt hash of their password. Never the plain password.
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)

    # Is this account active? We set to False to "soft delete" users
    # without actually removing their data.
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    # Is this user an admin? Admins can delete assets, normal users cannot.
    is_admin: Mapped[bool] = mapped_column(Boolean, default=False)

    # CONCEPT — Timestamps:
    # Keeping track of when records are created and updated is
    # standard practice. The `default` parameter runs at INSERT time.
    # `onupdate` runs automatically when a row is updated.
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc)
    )

    # CONCEPT — Relationships:
    # This tells SQLAlchemy that a User can have many Assets
    # and many Incidents. SQLAlchemy uses this to let you write
    # `user.assets` and get back a list of Asset objects.
    # back_populates="owner" means the Asset model also has a
    # relationship attribute called "owner" pointing back here.
    assets: Mapped[list["Asset"]] = relationship("Asset", back_populates="owner")
    incidents: Mapped[list["Incident"]] = relationship("Incident", back_populates="reporter")

    def __repr__(self) -> str:
        """
        CONCEPT — __repr__:
        This is what Python prints when you do print(user) in
        the terminal or in debug logs. Always define this — it
        makes debugging much easier.
        """
        return f"<User id={self.id} email={self.email}>"