from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from typing import Optional, List
from datetime import datetime
from uuid import UUID

from app.db import get_db
from app.models import Alert, AlertResponse, AlertListResponse, User
from app.auth import get_current_user

router = APIRouter()


@router.get("/", response_model=AlertListResponse)
async def get_alerts(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    host: Optional[str] = Query(None),
    severity: Optional[str] = Query(None),
    incident_id: Optional[UUID] = Query(None)
):
    query = select(Alert)
    
    # Apply filters
    if host:
        query = query.where(Alert.host == host)
    if severity:
        query = query.where(Alert.severity == severity)
    if incident_id:
        query = query.where(Alert.incident_id == incident_id)
    
    # Get total count
    count_query = select(func.count()).select_from(query.subquery())
    total_result = await db.execute(count_query)
    total = total_result.scalar()
    
    # Apply pagination
    query = query.order_by(Alert.timestamp.desc()).offset(skip).limit(limit)
    
    result = await db.execute(query)
    alerts = result.scalars().all()
    
    return AlertListResponse(
        alerts=[AlertResponse.from_orm(alert) for alert in alerts],
        total=total
    )


@router.get("/{alert_id}", response_model=AlertResponse)
async def get_alert(
    alert_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(select(Alert).where(Alert.id == alert_id))
    alert = result.scalar_one_or_none()
    
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")
    
    return AlertResponse.from_orm(alert)
