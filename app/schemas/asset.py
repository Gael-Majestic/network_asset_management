# ==============================================================
# app/schemas/asset.py
# ==============================================================

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field

from app.models.asset import AssetStatus, AssetType


class AssetBase(BaseModel):
    """
    Shared fields across all asset schemas.

    CONCEPT — Importing Enums into schemas:
    We reuse the same AssetType and AssetStatus enums from the
    model. This guarantees the API only accepts the exact same
    values the database accepts. No duplication, no mismatch.
    """
    name: str = Field(..., min_length=1, max_length=255, description="Asset name")
    asset_type: AssetType
    status: AssetStatus = AssetStatus.ACTIVE
    location: Optional[str] = Field(default=None, max_length=255)
    ip_address: Optional[str] = Field(default=None, max_length=45)
    tenant: str = Field(..., min_length=1, max_length=255, description="Company or site name")
    description: Optional[str] = None


class AssetCreate(AssetBase):
    """
    Schema for POST /assets
    Inherits all fields from AssetBase.
    No extra fields needed — owner_id is taken from the JWT token
    in the router (not from the request body).
    """
    pass


class AssetUpdate(BaseModel):
    """
    Schema for PATCH /assets/{id}
    Every field is Optional — the client sends only what they
    want to change.
    """
    name: Optional[str] = Field(default=None, min_length=1, max_length=255)
    asset_type: Optional[AssetType] = None
    status: Optional[AssetStatus] = None
    location: Optional[str] = None
    ip_address: Optional[str] = None
    tenant: Optional[str] = None
    description: Optional[str] = None


class AssetResponse(AssetBase):
    """
    Schema for API responses.
    Adds database-generated fields: id, owner_id, timestamps.
    """
    id: int
    owner_id: int
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}