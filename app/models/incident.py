# ==============================================================
# app/models/incident.py
#
# WHAT THIS FILE DOES:
#   Defines the "incidents" table — network or system problems
#   that are opened, tracked, and closed by engineers.
# ==============================================================

import enum
from datetime import datetime, timezone

from sqlalchemy import DateTime, Enum, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.database import Base


class IncidentSeverity(str, enum.Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class IncidentStatus(str, enum.Enum):
    OPEN = "open"
    IN_PROGRESS = "in_progress"
    RESOLVED = "resolved"
    CLOSED = "closed"


class Incident(Base):
    __tablename__ = "incidents"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=True)

    severity: Mapped[IncidentSeverity] = mapped_column(
        Enum(IncidentSeverity), default=IncidentSeverity.MEDIUM, nullable=False
    )

    status: Mapped[IncidentStatus] = mapped_column(
        Enum(IncidentStatus), default=IncidentStatus.OPEN, nullable=False
    )

    # Which asset this incident is about
    # nullable=True because some incidents may not be tied to a specific asset
    asset_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("assets.id"), nullable=True
    )

    # Who opened this incident
    reporter_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id"), nullable=False
    )

    # Free text field to record resolution steps
    resolution_notes: Mapped[str] = mapped_column(Text, nullable=True)

    # When was this incident resolved?
    resolved_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=True
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

    # Relationships
    asset: Mapped["Asset"] = relationship("Asset", back_populates="incidents")
    reporter: Mapped["User"] = relationship("User", back_populates="incidents")

    def __repr__(self) -> str:
        return f"<Incident id={self.id} title={self.title} status={self.status}>"