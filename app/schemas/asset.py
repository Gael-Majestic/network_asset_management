# ==============================================================
# app/schemas/asset.py
# ==============================================================

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field, model_validator

from app.models.asset import AssetStatus, AssetType
from app.schemas.validators import IPAddressStr, reject_nulls


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
    ip_address: Optional[IPAddressStr] = Field(default=None, max_length=45, description="IPv4 or IPv6 address")
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
    want to change. The limits match AssetBase, so an update
    cannot store a value that creating the asset would refuse.
    """

    name: Optional[str] = Field(default=None, min_length=1, max_length=255)
    asset_type: Optional[AssetType] = None
    status: Optional[AssetStatus] = None
    location: Optional[str] = Field(default=None, max_length=255)
    ip_address: Optional[IPAddressStr] = Field(default=None, max_length=45)
    tenant: Optional[str] = Field(default=None, min_length=1, max_length=255)
    description: Optional[str] = None

    @model_validator(mode="after")
    def required_columns_are_not_null(self):
        # location, ip_address and description may be cleared with null;
        # these four are NOT NULL in the database.
        reject_nulls(self, ("name", "asset_type", "status", "tenant"))
        return self


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
