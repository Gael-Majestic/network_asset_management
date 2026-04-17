# ==============================================================
# app/models/asset.py
#
# WHAT THIS FILE DOES:
#   Defines the "assets" table — the devices and infrastructure
#   components that companies track (routers, servers, etc.)
# ==============================================================

import enum
from datetime import datetime, timezone

from sqlalchemy import DateTime, Enum, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.database import Base


# ==============================================================
# CONCEPT — Python Enum:
# An Enum is a set of named constants. Using an Enum for
# columns that only accept specific values (like asset types)
# has two benefits:
#   1. Your Python code gets autocomplete and type safety
#   2. PostgreSQL enforces the valid values at the database level
#      (it will reject "SERVER_TYPO" automatically)
# ==============================================================
class AssetType(str, enum.Enum):
    ROUTER = "router"
    SWITCH = "switch"
    SERVER = "server"
    FIREWALL = "firewall"
    ACCESS_POINT = "access_point"
    VIRTUAL_MACHINE = "virtual_machine"
    CLOUD_INSTANCE = "cloud_instance"
    OTHER = "other"


class AssetStatus(str, enum.Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    MAINTENANCE = "maintenance"
    DECOMMISSIONED = "decommissioned"


class Asset(Base):
    __tablename__ = "assets"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    # The human-readable name of this asset e.g. "Core Router - Rustenburg DC"
    name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)

    # CONCEPT — Enum column:
    # SQLAlchemy's Enum() takes our Python enum class and creates
    # a PostgreSQL ENUM type in the database.
    asset_type: Mapped[AssetType] = mapped_column(
        Enum(AssetType), nullable=False
    )

    status: Mapped[AssetStatus] = mapped_column(
        Enum(AssetStatus), default=AssetStatus.ACTIVE, nullable=False
    )

    # Physical or logical location e.g. "Server Room B", "AWS af-south-1"
    location: Mapped[str] = mapped_column(String(255), nullable=True)

    # IP address — stored as a string for simplicity
    ip_address: Mapped[str] = mapped_column(String(45), nullable=True)

    # Which company/tenant this asset belongs to
    tenant: Mapped[str] = mapped_column(String(255), nullable=False, index=True)

    # Free-form description of the asset
    description: Mapped[str] = mapped_column(Text, nullable=True)

    # CONCEPT — Foreign Key:
    # ForeignKey("users.id") creates a link between this table
    # and the users table. It means: every asset must be owned
    # by a user that exists in the users table.
    # PostgreSQL enforces this — you cannot create an asset
    # with an owner_id that does not exist in users.
    owner_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id"), nullable=False
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc)
    )

    # Relationship back to the User who owns this asset
    owner: Mapped["User"] = relationship("User", back_populates="assets")

    # One asset can have many incidents
    incidents: Mapped[list["Incident"]] = relationship("Incident", back_populates="asset")

    def __repr__(self) -> str:
        return f"<Asset id={self.id} name={self.name} type={self.asset_type}>"