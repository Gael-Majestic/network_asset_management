# ==============================================================
# app/schemas/incident.py
# ==============================================================

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field

from app.models.incident import IncidentSeverity, IncidentStatus


class IncidentBase(BaseModel):
    title: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    severity: IncidentSeverity = IncidentSeverity.MEDIUM
    asset_id: Optional[int] = Field(
        default=None,
        description="ID of the affected asset. Optional — some incidents are not tied to a specific asset."
    )


class IncidentCreate(IncidentBase):
    """
    Schema for POST /incidents
    reporter_id comes from the JWT token in the router,
    not from the request body. The logged-in user IS the reporter.
    """
    pass


class IncidentUpdate(BaseModel):
    """
    Schema for PATCH /incidents/{id}

    CONCEPT — Status transitions:
    In a real system you might enforce that status can only move
    forward (open → in_progress → resolved → closed).
    For this project we keep it simple and allow any update.
    You could add a validator here later using @field_validator.
    """
    title: Optional[str] = Field(default=None, min_length=1, max_length=255)
    description: Optional[str] = None
    severity: Optional[IncidentSeverity] = None
    status: Optional[IncidentStatus] = None
    resolution_notes: Optional[str] = None


class IncidentResponse(IncidentBase):
    """
    Schema for API responses.
    """
    id: int
    status: IncidentStatus
    reporter_id: int
    resolution_notes: Optional[str] = None
    resolved_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}