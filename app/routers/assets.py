# ==============================================================
# app/routers/assets.py
#
# WHAT THIS FILE DOES:
#   Full CRUD for assets.
#   Endpoints:
#     GET    /assets          → list assets (with optional filters)
#     GET    /assets/{id}     → get a single asset
#     POST   /assets          → create a new asset
#     PATCH  /assets/{id}     → update an asset
#     DELETE /assets/{id}     → delete an asset (admin only)
# ==============================================================

from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.db.database import get_db
from app.dependencies import get_current_admin_user, get_current_user
from app.models.asset import Asset, AssetStatus, AssetType
from app.models.user import User
from app.schemas.asset import AssetCreate, AssetResponse, AssetUpdate

router = APIRouter(prefix="/assets", tags=["Assets"])


@router.get(
    "/",
    response_model=List[AssetResponse],
    summary="List all assets",
)
async def list_assets(
    # CONCEPT — Query parameters:
    # These are optional URL parameters: /assets?tenant=Kamoa&status=active
    # Query() lets us add validation and documentation for each.
    # The `= None` means they are optional — if not provided, no filter applied.
    tenant: Optional[str] = Query(default=None, description="Filter by tenant/company name"),
    asset_type: Optional[AssetType] = Query(default=None, description="Filter by asset type"),
    status: Optional[AssetStatus] = Query(default=None, description="Filter by asset status"),
    skip: int = Query(default=0, ge=0, description="Number of records to skip (for pagination)"),
    limit: int = Query(default=50, ge=1, le=200, description="Maximum records to return"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),   # Requires login
):
    """
    CONCEPT — Dynamic query building:
    We start with a base query and add WHERE clauses
    conditionally based on which filters were provided.
    This avoids writing separate queries for every combination.

    CONCEPT — Pagination with skip and limit:
    Returning ALL records at once is dangerous with large datasets.
    skip=0, limit=50 returns the first 50 records.
    skip=50, limit=50 returns the next 50 (page 2).
    This is called "offset pagination" — simple and effective.
    """
    query = select(Asset)

    if tenant:
        query = query.where(Asset.tenant == tenant)
    if asset_type:
        query = query.where(Asset.asset_type == asset_type)
    if status:
        query = query.where(Asset.status == status)

    # CONCEPT — offset() and limit():
    # These map directly to SQL: OFFSET 0 LIMIT 50
    query = query.offset(skip).limit(limit)

    result = await db.execute(query)
    assets = result.scalars().all()

    # CONCEPT — scalars().all():
    # db.execute() returns a result object.
    # .scalars() extracts just the model objects (not raw tuples).
    # .all() converts to a Python list.
    return assets


@router.get(
    "/{asset_id}",
    response_model=AssetResponse,
    summary="Get a single asset by ID",
)
async def get_asset(
    asset_id: int,   # FastAPI extracts this from the URL path automatically
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    CONCEPT — Path parameters:
    `{asset_id}` in the route path becomes the `asset_id: int`
    parameter in the function. FastAPI extracts and validates it.
    If someone calls /assets/abc (not an int), FastAPI returns
    a 422 error automatically.
    """
    result = await db.execute(
        select(Asset).where(Asset.id == asset_id)
    )
    asset = result.scalar_one_or_none()

    if asset is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Asset with id {asset_id} not found"
        )

    return asset


@router.post(
    "/",
    response_model=AssetResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new asset",
)
async def create_asset(
    asset_data: AssetCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    CONCEPT — Reading from the JWT token:
    Notice the client does NOT send owner_id in the request body.
    We get it from `current_user.id` — the authenticated user.
    This is a security pattern: you cannot create assets
    on behalf of someone else by sending a different owner_id.
    The server decides who the owner is, not the client.
    """
    new_asset = Asset(
        **asset_data.model_dump(),    # Unpack all schema fields into keyword arguments
        owner_id=current_user.id,     # Set owner from the JWT, not from request body
    )

    # CONCEPT — model_dump():
    # This is Pydantic's method to convert a schema object to a dict.
    # Asset(**asset_data.model_dump()) is equivalent to:
    # Asset(name=asset_data.name, asset_type=asset_data.asset_type, ...)
    # The ** operator unpacks the dict into keyword arguments.

    db.add(new_asset)
    await db.flush()
    await db.refresh(new_asset)
    return new_asset


@router.patch(
    "/{asset_id}",
    response_model=AssetResponse,
    summary="Update an asset",
)
async def update_asset(
    asset_id: int,
    asset_data: AssetUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    CONCEPT — Partial update with PATCH:
    PATCH means "change only the fields I send."
    The client can send just {"status": "maintenance"} and
    only that field changes. Everything else stays the same.

    model_dump(exclude_unset=True) is the key:
    It returns only the fields the client actually sent,
    excluding fields that were not included in the request.
    Without exclude_unset=True, all Optional fields would
    be included as None, wiping out existing values.
    """

    # Step 1: Fetch the existing record
    result = await db.execute(
        select(Asset).where(Asset.id == asset_id)
    )
    asset = result.scalar_one_or_none()

    if asset is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Asset with id {asset_id} not found"
        )

    # Step 2: Only asset owner or admin can update
    if asset.owner_id != current_user.id and not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to update this asset"
        )

    # Step 3: Apply only the sent fields
    update_data = asset_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(asset, field, value)

    # CONCEPT — setattr():
    # setattr(obj, "name", "new_value") is the same as obj.name = "new_value"
    # but works when the field name is a variable string.
    # This loop applies all updates dynamically without hardcoding field names.

    await db.flush()
    await db.refresh(asset)
    return asset


@router.delete(
    "/{asset_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete an asset (admin only)",
)
async def delete_asset(
    asset_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_admin_user),  # Admin only
):
    """
    CONCEPT — HTTP 204 No Content:
    A successful DELETE returns 204 — no body, no content.
    This is the REST standard for deletions.
    Notice we use get_current_admin_user here instead of
    get_current_user — only admins can delete assets.
    """
    result = await db.execute(
        select(Asset).where(Asset.id == asset_id)
    )
    asset = result.scalar_one_or_none()

    if asset is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Asset with id {asset_id} not found"
        )

    await db.delete(asset)