from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, update
from typing import Optional, List
from datetime import datetime
from uuid import UUID

from app.db import get_db
from app.models import (
    Incident, Alert, IncidentResponse, IncidentListResponse, 
    IncidentStatus, IncidentAnalyzeRequest, IncidentCloseRequest, User
)
from app.auth import get_current_user
from app.services.llm_service import LLMService

router = APIRouter()


@router.get("/", response_model=IncidentListResponse)
async def get_incidents(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    skip: int = 0,
    limit: int = 100,
    host: Optional[str] = None,
    status: Optional[IncidentStatus] = None
):
    query = select(Incident)
    
    # Apply filters
    if host:
        query = query.where(Incident.host == host)
    if status:
        query = query.where(Incident.status == status)
    
    # Get total count
    count_query = select(func.count()).select_from(query.subquery())
    total_result = await db.execute(count_query)
    total = total_result.scalar()
    
    # Apply pagination
    query = query.order_by(Incident.created_at.desc()).offset(skip).limit(limit)
    
    result = await db.execute(query)
    incidents = result.scalars().all()
    
    # Get alerts for each incident
    incident_responses = []
    for incident in incidents:
        # Get alerts for this incident
        alerts_query = select(Alert).where(Alert.incident_id == incident.id).order_by(Alert.timestamp.desc())
        alerts_result = await db.execute(alerts_query)
        alerts = alerts_result.scalars().all()
        
        incident_response = IncidentResponse.from_orm(incident)
        incident_response.alerts = [AlertResponse.from_orm(alert) for alert in alerts]
        incident_responses.append(incident_response)
    
    return IncidentListResponse(
        incidents=incident_responses,
        total=total
    )


@router.get("/{incident_id}", response_model=IncidentResponse)
async def get_incident(
    incident_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    # Get incident
    incident_result = await db.execute(select(Incident).where(Incident.id == incident_id))
    incident = incident_result.scalar_one_or_none()
    
    if not incident:
        raise HTTPException(status_code=404, detail="Incident not found")
    
    # Get alerts for this incident
    alerts_query = select(Alert).where(Alert.incident_id == incident.id).order_by(Alert.timestamp.desc())
    alerts_result = await db.execute(alerts_query)
    alerts = alerts_result.scalars().all()
    
    incident_response = IncidentResponse.from_orm(incident)
    incident_response.alerts = [AlertResponse.from_orm(alert) for alert in alerts]
    
    return incident_response


@router.post("/{incident_id}/analyze")
async def analyze_incident(
    incident_id: UUID,
    request: IncidentAnalyzeRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    # Get incident
    incident_result = await db.execute(select(Incident).where(Incident.id == incident_id))
    incident = incident_result.scalar_one_or_none()
    
    if not incident:
        raise HTTPException(status_code=404, detail="Incident not found")
    
    # Get alerts for this incident
    alerts_query = select(Alert).where(Alert.incident_id == incident_id).order_by(Alert.timestamp.desc())
    alerts_result = await db.execute(alerts_query)
    alerts = alerts_result.scalars().all()
    
    if not alerts:
        raise HTTPException(status_code=400, detail="No alerts found for this incident")
    
    # Analyze with LLM
    llm_service = LLMService()
    alerts_data = [
        {
            "severity": alert.severity,
            "message": alert.message,
            "timestamp": alert.timestamp.isoformat()
        }
        for alert in alerts
    ]
    
    try:
        analysis = await llm_service.analyze_alerts(alerts_data)
        
        # Update incident with analysis
        incident.root_cause_summary = analysis.root_cause
        incident.llm_explanation = analysis.reasoning
        incident.updated_at = datetime.utcnow()
        
        await db.commit()
        await db.refresh(incident)
        
        return {"message": "Analysis completed", "root_cause": analysis.root_cause}
        
    except Exception as e:
        raise HTTPException(
            status_code=500, 
            detail=f"LLM analysis failed: {str(e)}"
        )


@router.post("/{incident_id}/close")
async def close_incident(
    incident_id: UUID,
    request: IncidentCloseRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    # Get incident
    incident_result = await db.execute(select(Incident).where(Incident.id == incident_id))
    incident = incident_result.scalar_one_or_none()
    
    if not incident:
        raise HTTPException(status_code=404, detail="Incident not found")
    
    if incident.status == IncidentStatus.CLOSED:
        raise HTTPException(status_code=400, detail="Incident is already closed")
    
    # Close incident
    incident.status = IncidentStatus.CLOSED
    incident.updated_at = datetime.utcnow()
    
    await db.commit()
    
    return {"message": "Incident closed successfully"}
