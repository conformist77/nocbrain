import asyncio
import aiohttp
import json
import logging
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.config import settings
from app.db import AsyncSessionLocal
from app.models import Alert, ZabbixProblem

logger = logging.getLogger(__name__)


class ZabbixClient:
    def __init__(self):
        self.base_url = settings.zabbix_url
        self.username = settings.zabbix_user
        self.password = settings.zabbix_password
        self.auth_token = None
        self.session = None
    
    async def _get_session(self):
        if not self.session:
            self.session = aiohttp.ClientSession()
        return self.session
    
    async def _login(self) -> str:
        """Authenticate with Zabbix API"""
        if not self.base_url or not self.username or not self.password:
            logger.warning("Zabbix credentials not configured")
            return None
        
        session = await self._get_session()
        
        payload = {
            "jsonrpc": "2.0",
            "method": "user.login",
            "params": {
                "user": self.username,
                "password": self.password
            },
            "id": 1,
            "auth": None
        }
        
        try:
            async with session.post(self.base_url, json=payload) as response:
                if response.status == 200:
                    data = await response.json()
                    if "result" in data:
                        self.auth_token = data["result"]
                        logger.info("Successfully authenticated with Zabbix")
                        return self.auth_token
                    else:
                        logger.error(f"Zabbix login failed: {data}")
                        return None
                else:
                    logger.error(f"Zabbix login HTTP error: {response.status}")
                    return None
        except Exception as e:
            logger.error(f"Zabbix login exception: {e}")
            return None
    
    async def get_problems(self) -> List[ZabbixProblem]:
        """Get active problems from Zabbix"""
        if not self.auth_token:
            await self._login()
        
        if not self.auth_token:
            return []
        
        session = await self._get_session()
        
        payload = {
            "jsonrpc": "2.0",
            "method": "problem.get",
            "params": {
                "output": "extend",
                "selectAcknowledges": "extend",
                "selectTags": "extend",
                "recent": "true",
                "sortfield": ["eventid"],
                "sortorder": "DESC"
            },
            "auth": self.auth_token,
            "id": 2
        }
        
        try:
            async with session.post(self.base_url, json=payload) as response:
                if response.status == 200:
                    data = await response.json()
                    if "result" in data:
                        problems = []
                        for problem in data["result"]:
                            zabbix_problem = ZabbixProblem(
                                eventid=problem.get("eventid", ""),
                                objectid=problem.get("objectid", ""),
                                name=problem.get("name", ""),
                                severity=self._map_severity(problem.get("severity", "0")),
                                host=problem.get("host", ""),
                                clock=problem.get("clock", ""),
                                value=problem.get("value", ""),
                                acknowledged=problem.get("acknowledged", "0"),
                                status=problem.get("status", "0")
                            )
                            problems.append(zabbix_problem)
                        return problems
                    else:
                        logger.error(f"No problems returned from Zabbix: {data}")
                        return []
                else:
                    logger.error(f"Zabbix problems HTTP error: {response.status}")
                    return []
        except Exception as e:
            logger.error(f"Zabbix problems exception: {e}")
            return []
    
    def _map_severity(self, zabbix_severity: str) -> str:
        """Map Zabbix severity to internal severity"""
        severity_map = {
            "0": "info",
            "1": "info", 
            "2": "warning",
            "3": "average",
            "4": "high",
            "5": "disaster"
        }
        return severity_map.get(zabbix_severity, "info")
    
    async def save_alerts(self, problems: List[ZabbixProblem]) -> List[Alert]:
        """Save Zabbix problems as alerts"""
        if not problems:
            return []
        
        async with AsyncSessionLocal() as db:
            saved_alerts = []
            
            for problem in problems:
                # Check if alert already exists
                existing_query = select(Alert).where(Alert.raw_payload.op('->>')('eventid') == problem.eventid)
                existing_result = await db.execute(existing_query)
                existing_alert = existing_result.scalar_one_or_none()
                
                if existing_alert:
                    continue
                
                # Create new alert
                alert = Alert(
                    host=problem.host,
                    severity=problem.severity,
                    message=problem.name,
                    timestamp=datetime.fromtimestamp(int(problem.clock)) if problem.clock else datetime.utcnow(),
                    raw_payload={
                        "eventid": problem.eventid,
                        "objectid": problem.objectid,
                        "acknowledged": problem.acknowledged,
                        "status": problem.status,
                        "source": "zabbix"
                    }
                )
                
                db.add(alert)
                saved_alerts.append(alert)
            
            await db.commit()
            
            # Refresh to get IDs
            for alert in saved_alerts:
                await db.refresh(alert)
            
            logger.info(f"Saved {len(saved_alerts)} new alerts from Zabbix")
            return saved_alerts
    
    async def start_ingestion(self):
        """Start continuous ingestion from Zabbix"""
        logger.info("Starting Zabbix ingestion")
        
        while True:
            try:
                # Get problems from Zabbix
                problems = await self.get_problems()
                
                # Save as alerts
                await self.save_alerts(problems)
                
                # Wait before next poll
                await asyncio.sleep(60)  # Poll every minute
                
            except Exception as e:
                logger.error(f"Error in Zabbix ingestion: {e}")
                await asyncio.sleep(60)  # Wait before retry
