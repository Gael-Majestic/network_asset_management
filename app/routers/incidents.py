# ==============================================================
# app/routers/incidents.py
#
# WHAT THIS FILE DOES:
#   Full CRUD for incidents.
#   Endpoints:
#     GET    /incidents        → list incidents (with filters)
#     GET    /incidents/{id}   → get a single incident
#     POST   /incidents        → open a new incident
#     PATCH  /incidents/{id}   → update an incident (status, notes)
#     DELETE /incidents/{id}   → delete (admin only)
# ==============================================================

from datetime import datetime, timezone
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.db.database import get_db
from app.dependencies import get_current_admin_user, get_current_user
from app.models.incident import Incident, IncidentSeverity, IncidentStatus
from app.models.user import User
from app.schemas.incident import IncidentCreate, IncidentResponse, IncidentUpdate

router = APIRouter(prefix="/incidents", tags=["Incidents"])


@router.get(
    "/",
    response_model=List[IncidentResponse],
    summary="List all incidents",
)
async def list_incidents(
    status: Optional[IncidentStatus] = Query(default=None),
    severity: Optional[IncidentSeverity] = Query(default=None),
    asset_id: Optional[int] = Query(default=None, description="Filter by affected asset"),
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=50, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    query = select(Incident)

    if status:
        query = query.where(Incident.status == status)
    if severity:
        query = query.where(Incident.severity == severity)
    if asset_id:
        query = query.where(Incident.asset_id == asset_id)

    query = query.offset(skip).limit(limit)
    result = await db.execute(query)
    return result.scalars().all()


@router.get(
    "/{incident_id}",
    response_model=IncidentResponse,
    summary="Get a single incident by ID",
)
async def get_incident(
    incident_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(Incident).where(Incident.id == incident_id)
    )
    incident = result.scalar_one_or_none()

    if incident is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Incident with id {incident_id} not found"
        )
    return incident


@router.post(
    "/",
    response_model=IncidentResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Open a new incident",
)
async def create_incident(
    incident_data: IncidentCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    new_incident = Incident(
        **incident_data.model_dump(),
        reporter_id=current_user.id,
    )
    db.add(new_incident)
    await db.flush()
    await db.refresh(new_incident)
    return new_incident


@router.patch(
    "/{incident_id}",
    response_model=IncidentResponse,
    summary="Update an incident",
)
async def update_incident(
    incident_id: int,
    incident_data: IncidentUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(Incident).where(Incident.id == incident_id)
    )
    incident = result.scalar_one_or_none()

    if incident is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Incident with id {incident_id} not found"
        )

    update_data = incident_data.model_dump(exclude_unset=True)

    # CONCEPT — Business logic in the router:
    # When an incident is marked as resolved, we automatically
    # record the exact timestamp. The client does not need to
    # send a resolved_at value — the server sets it.
    # This is an example of server-side business logic that
    # the API enforces regardless of what the client sends.
    if update_data.get("status") == IncidentStatus.RESOLVED:
        update_data["resolved_at"] = datetime.now(timezone.utc)

    for field, value in update_data.items():
        setattr(incident, field, value)

    await db.flush()
    await db.refresh(incident)
    return incident


@router.delete(
    "/{incident_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete an incident (admin only)",
)
async def delete_incident(
    incident_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_admin_user),
):
    result = await db.execute(
        select(Incident).where(Incident.id == incident_id)
    )
    incident = result.scalar_one_or_none()

    if incident is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Incident with id {incident_id} not found"
        )

    await db.delete(incident)