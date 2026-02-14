import asyncio
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, update

from app.db import AsyncSessionLocal
from app.models import Alert, Incident, IncidentStatus

logger = logging.getLogger(__name__)


class CorrelationEngine:
    def __init__(self):
        self.correlation_window_minutes = 5
        self.alert_threshold = 5
    
    async def start_correlation(self):
        """Start continuous correlation of alerts"""
        logger.info("Starting alert correlation engine")
        
        while True:
            try:
                await self.correlate_alerts()
                await asyncio.sleep(30)  # Run every 30 seconds
                
            except Exception as e:
                logger.error(f"Error in correlation engine: {e}")
                await asyncio.sleep(30)  # Wait before retry
    
    async def correlate_alerts(self):
        """Correlate alerts into incidents"""
        async with AsyncSessionLocal() as db:
            # Get uncorrelated alerts within the correlation window
            correlation_time = datetime.utcnow() - timedelta(minutes=self.correlation_window_minutes)
            
            query = select(Alert).where(
                and_(
                    Alert.incident_id.is_(None),
                    Alert.timestamp >= correlation_time
                )
            ).order_by(Alert.timestamp.desc())
            
            result = await db.execute(query)
            uncorrelated_alerts = result.scalars().all()
            
            if not uncorrelated_alerts:
                return
            
            # Group alerts by host
            alerts_by_host = {}
            for alert in uncorrelated_alerts:
                if alert.host not in alerts_by_host:
                    alerts_by_host[alert.host] = []
                alerts_by_host[alert.host].append(alert)
            
            # Create incidents for hosts with threshold alerts
            incidents_created = 0
            for host, host_alerts in alerts_by_host.items():
                if len(host_alerts) >= self.alert_threshold:
                    # Check if there's already an open incident for this host
                    existing_incident_query = select(Incident).where(
                        and_(
                            Incident.host == host,
                            Incident.status == IncidentStatus.OPEN
                        )
                    ).order_by(Incident.created_at.desc())
                    
                    existing_result = await db.execute(existing_incident_query)
                    existing_incident = existing_result.scalar_one_or_none()
                    
                    if existing_incident:
                        # Attach alerts to existing incident
                        for alert in host_alerts:
                            alert.incident_id = existing_incident.id
                        logger.info(f"Attached {len(host_alerts)} alerts to existing incident for host {host}")
                    else:
                        # Create new incident
                        incident = Incident(
                            host=host,
                            status=IncidentStatus.OPEN,
                            created_at=datetime.utcnow()
                        )
                        
                        db.add(incident)
                        await db.flush()  # Get incident ID
                        
                        # Attach alerts to new incident
                        for alert in host_alerts:
                            alert.incident_id = incident.id
                        
                        incidents_created += 1
                        logger.info(f"Created new incident for host {host} with {len(host_alerts)} alerts")
            
            if incidents_created > 0:
                await db.commit()
                logger.info(f"Created {incidents_created} new incidents")
            else:
                await db.commit()
    
    async def get_correlation_stats(self) -> Dict[str, Any]:
        """Get correlation statistics"""
        async with AsyncSessionLocal() as db:
            # Get total alerts
            alerts_query = select(Alert)
            alerts_result = await db.execute(alerts_query)
            total_alerts = len(alerts_result.scalars().all())
            
            # Get correlated alerts
            correlated_query = select(Alert).where(Alert.incident_id.isnot(None))
            correlated_result = await db.execute(correlated_query)
            correlated_alerts = len(correlated_result.scalars().all())
            
            # Get total incidents
            incidents_query = select(Incident)
            incidents_result = await db.execute(incidents_query)
            total_incidents = len(incidents_result.scalars().all())
            
            # Get open incidents
            open_incidents_query = select(Incident).where(Incident.status == IncidentStatus.OPEN)
            open_result = await db.execute(open_incidents_query)
            open_incidents = len(open_result.scalars().all())
            
            return {
                "total_alerts": total_alerts,
                "correlated_alerts": correlated_alerts,
                "uncorrelated_alerts": total_alerts - correlated_alerts,
                "total_incidents": total_incidents,
                "open_incidents": open_incidents,
                "correlation_rate": (correlated_alerts / total_alerts * 100) if total_alerts > 0 else 0
            }
