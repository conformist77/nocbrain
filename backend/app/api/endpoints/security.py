"""
NOCbRAIN Security Analysis API Endpoints
Integration with security pattern engine for threat detection
"""

from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Dict, Any, Optional
from datetime import datetime

from app.core.database import get_db
from app.core.security import get_current_active_user, check_permissions
from app.models.user import User
from app.security_analyzer.pattern_engine import pattern_engine
from app.schemas.security import (
    LogAnalysisRequest, LogAnalysisResponse,
    ThreatAlertRequest, ThreatAlertResponse,
    SecurityStatsResponse
)
from app.core.logging import get_logger

logger = get_logger(__name__)

router = APIRouter()


@router.post("/analyze-log", response_model=LogAnalysisResponse)
async def analyze_security_log(
    request: LogAnalysisRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(check_permissions(["security:analyze"]))
) -> Any:
    """Analyze security log for threats using pattern engine"""
    try:
        # Analyze log through pattern engine
        threats = await pattern_engine.analyze_log(request.log_data)
        
        response = LogAnalysisResponse(
            log_id=request.log_data.get("id", "unknown"),
            threats_detected=len(threats),
            threats=threats,
            timestamp=datetime.utcnow().isoformat()
        )
        
        # Log analysis in background
        background_tasks.add_task(
            _log_security_analysis,
            current_user.id,
            request.log_data,
            threats
        )
        
        logger.info(f"Security log analyzed for user {current_user.username}: {len(threats)} threats")
        return response
        
    except Exception as e:
        logger.error(f"Failed to analyze security log: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to analyze security log"
        )


@router.post("/analyze-batch", response_model=List[LogAnalysisResponse])
async def analyze_batch_logs(
    logs: List[Dict[str, Any]],
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(check_permissions(["security:analyze"]))
) -> Any:
    """Analyze multiple security logs in batch"""
    try:
        # Analyze logs through pattern engine
        all_threats = await pattern_engine.analyze_batch(logs)
        
        # Build responses
        responses = []
        for i, log in enumerate(logs):
            threats = all_threats[i] if i < len(all_threats) else []
            response = LogAnalysisResponse(
                log_id=log.get("id", f"batch_{i}"),
                threats_detected=len(threats),
                threats=threats,
                timestamp=datetime.utcnow().isoformat()
            )
            responses.append(response)
        
        # Log batch analysis in background
        background_tasks.add_task(
            _log_batch_security_analysis,
            current_user.id,
            logs,
            all_threats
        )
        
        logger.info(f"Batch security analysis completed for user {current_user.username}: {len(logs)} logs")
        return responses
        
    except Exception as e:
        logger.error(f"Failed to analyze batch security logs: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to analyze batch security logs"
        )


@router.get("/threats/summary")
async def get_threat_summary(
    time_window: int = 3600,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(check_permissions(["security:read"]))
) -> Any:
    """Get threat summary for time window"""
    try:
        summary = await pattern_engine.get_threat_summary(time_window)
        return summary
        
    except Exception as e:
        logger.error(f"Failed to get threat summary: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get threat summary"
        )


@router.post("/patterns/add")
async def add_security_pattern(
    name: str,
    threat_type: str,
    severity: str,
    description: str,
    patterns: List[str],
    conditions: Dict[str, Any],
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(check_permissions(["security:admin"]))
) -> Any:
    """Add custom security pattern"""
    try:
        from app.security_analyzer.pattern_engine import SecurityPattern, ThreatType, SeverityLevel
        
        # Create pattern
        pattern = SecurityPattern(
            name=name,
            threat_type=ThreatType(threat_type),
            severity=SeverityLevel[severity.upper()],
            description=description,
            patterns=patterns,
            conditions=conditions
        )
        
        # Add to pattern engine
        result = await pattern_engine.add_custom_pattern(pattern)
        
        if result["status"] == "error":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Failed to add pattern: {result['error']}"
            )
        
        logger.info(f"Security pattern added by user {current_user.username}: {name}")
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to add security pattern: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to add security pattern"
        )


@router.get("/patterns")
async def get_security_patterns(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(check_permissions(["security:read"]))
) -> Any:
    """Get all security patterns"""
    try:
        patterns = []
        for pattern in pattern_engine.patterns:
            patterns.append({
                "name": pattern.name,
                "threat_type": pattern.threat_type.value,
                "severity": pattern.severity.value,
                "description": pattern.description,
                "patterns": pattern.patterns,
                "conditions": pattern.conditions,
                "tags": pattern.tags
            })
        
        return {
            "patterns": patterns,
            "total_patterns": len(patterns),
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Failed to get security patterns: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get security patterns"
        )


@router.get("/stats", response_model=SecurityStatsResponse)
async def get_security_stats(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(check_permissions(["security:read"]))
) -> Any:
    """Get security analyzer statistics"""
    try:
        stats = await pattern_engine.get_stats()
        
        return SecurityStatsResponse(
            total_events=stats["total_events"],
            threats_detected=stats["threats_detected"],
            false_positives=stats["false_positives"],
            total_patterns=stats["total_patterns"],
            event_history_size=stats["event_history_size"],
            ip_reputation_size=stats["ip_reputation_size"],
            user_behavior_size=stats["user_behavior_size"],
            patterns_matched=dict(stats["patterns_matched"]),
            timestamp=stats["timestamp"]
        )
        
    except Exception as e:
        logger.error(f"Failed to get security stats: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get security stats"
        )


@router.get("/health")
async def security_health_check() -> Any:
    """Health check for security analyzer"""
    try:
        stats = await pattern_engine.get_stats()
        
        return {
            "status": "healthy",
            "service": "Security Analyzer",
            "total_events": stats["total_events"],
            "threats_detected": stats["threats_detected"],
            "active_patterns": stats["total_patterns"],
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Security health check failed: {e}")
        return {
            "status": "error",
            "service": "Security Analyzer",
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat()
        }


@router.post("/test-brute-force")
async def test_brute_force_detection(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(check_permissions(["security:test"]))
) -> Any:
    """Test brute force detection with sample logs"""
    try:
        # Sample brute force logs
        test_logs = [
            {
                "id": "test_bf_1",
                "timestamp": datetime.utcnow().isoformat(),
                "source_ip": "192.168.1.100",
                "message": "Failed password for root from 192.168.1.100 port 22 ssh2",
                "severity": "warning",
                "event_type": "authentication"
            },
            {
                "id": "test_bf_2",
                "timestamp": datetime.utcnow().isoformat(),
                "source_ip": "192.168.1.100",
                "message": "Failed password for root from 192.168.1.100 port 22 ssh2",
                "severity": "warning",
                "event_type": "authentication"
            },
            {
                "id": "test_bf_3",
                "timestamp": datetime.utcnow().isoformat(),
                "source_ip": "192.168.1.100",
                "message": "Failed password for root from 192.168.1.100 port 22 ssh2",
                "severity": "warning",
                "event_type": "authentication"
            },
            {
                "id": "test_bf_4",
                "timestamp": datetime.utcnow().isoformat(),
                "source_ip": "192.168.1.100",
                "message": "Failed password for root from 192.168.1.100 port 22 ssh2",
                "severity": "warning",
                "event_type": "authentication"
            },
            {
                "id": "test_bf_5",
                "timestamp": datetime.utcnow().isoformat(),
                "source_ip": "192.168.1.100",
                "message": "Failed password for root from 192.168.1.100 port 22 ssh2",
                "severity": "warning",
                "event_type": "authentication"
            }
        ]
        
        # Analyze test logs
        threats = await pattern_engine.analyze_batch(test_logs)
        
        # Count brute force threats
        brute_force_threats = [
            threat for threat_list in threats 
            for threat in threat_list 
            if threat.get("threat_type") == "brute_force"
        ]
        
        return {
            "test_type": "brute_force_detection",
            "test_logs": len(test_logs),
            "threats_detected": len(brute_force_threats),
            "threats": brute_force_threats,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Failed to test brute force detection: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to test brute force detection"
        )


@router.post("/test-port-scan")
async def test_port_scan_detection(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(check_permissions(["security:test"]))
) -> Any:
    """Test port scan detection with sample logs"""
    try:
        # Sample port scan logs
        test_logs = [
            {
                "id": "test_ps_1",
                "timestamp": datetime.utcnow().isoformat(),
                "source_ip": "192.168.1.200",
                "message": "Port scan detected from 192.168.1.200",
                "severity": "warning",
                "event_type": "network"
            },
            {
                "id": "test_ps_2",
                "timestamp": datetime.utcnow().isoformat(),
                "source_ip": "192.168.1.200",
                "message": "Connection attempt to port 22 from 192.168.1.200",
                "severity": "info",
                "event_type": "network"
            },
            {
                "id": "test_ps_3",
                "timestamp": datetime.utcnow().isoformat(),
                "source_ip": "192.168.1.200",
                "message": "Connection attempt to port 80 from 192.168.1.200",
                "severity": "info",
                "event_type": "network"
            },
            {
                "id": "test_ps_4",
                "timestamp": datetime.utcnow().isoformat(),
                "source_ip": "192.168.1.200",
                "message": "Connection attempt to port 443 from 192.168.1.200",
                "severity": "info",
                "event_type": "network"
            },
            {
                "id": "test_ps_5",
                "timestamp": datetime.utcnow().isoformat(),
                "source_ip": "192.168.1.200",
                "message": "Connection attempt to port 3389 from 192.168.1.200",
                "severity": "info",
                "event_type": "network"
            }
        ]
        
        # Analyze test logs
        threats = await pattern_engine.analyze_batch(test_logs)
        
        # Count port scan threats
        port_scan_threats = [
            threat for threat_list in threats 
            for threat in threat_list 
            if threat.get("threat_type") == "lateral_movement"
        ]
        
        return {
            "test_type": "port_scan_detection",
            "test_logs": len(test_logs),
            "threats_detected": len(port_scan_threats),
            "threats": port_scan_threats,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Failed to test port scan detection: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to test port scan detection"
        )


# Background tasks
async def _log_security_analysis(user_id: int, log_data: Dict[str, Any], threats: List[Dict[str, Any]]):
    """Log security analysis result to database"""
    try:
        logger.info(f"Security analysis result for user {user_id}: {len(threats)} threats")
    except Exception as e:
        logger.error(f"Failed to log security analysis result: {e}")


async def _log_batch_security_analysis(user_id: int, logs: List[Dict[str, Any]], all_threats: List[List[Dict[str, Any]]]):
    """Log batch security analysis result to database"""
    try:
        total_threats = sum(len(threats) for threats in all_threats)
        logger.info(f"Batch security analysis result for user {user_id}: {len(logs)} logs, {total_threats} threats")
    except Exception as e:
        logger.error(f"Failed to log batch security analysis result: {e}")
