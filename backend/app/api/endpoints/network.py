from fastapi import APIRouter, Depends, HTTPException, status, WebSocket, WebSocketDisconnect
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Any, Dict
from datetime import datetime

from app.core.database import get_db
from app.core.security import get_current_active_user, check_permissions
from app.models.user import User
from app.schemas.network import (
    DeviceCreate, DeviceResponse, DeviceUpdate,
    NetworkTopologyResponse, NetworkMetricsResponse,
    SNMPConfig, NetworkScanRequest
)
from app.modules.network.service import NetworkService
from app.core.logging import get_logger

router = APIRouter()
logger = get_logger(__name__)
network_service = NetworkService()


@router.post("/devices", response_model=DeviceResponse)
async def create_device(
    device: DeviceCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(check_permissions(["network:write"]))
) -> Any:
    """Add a new network device for monitoring"""
    try:
        result = await network_service.add_device(db, device, current_user.id)
        logger.info(f"Device {device.name} added by user {current_user.username}")
        return result
    except Exception as e:
        logger.error(f"Failed to add device {device.name}: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.get("/devices", response_model=List[DeviceResponse])
async def get_devices(
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(check_permissions(["network:read"]))
) -> Any:
    """Get list of monitored network devices"""
    try:
        devices = await network_service.get_devices(db, skip, limit, current_user.id)
        return devices
    except Exception as e:
        logger.error(f"Failed to get devices: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve devices"
        )


@router.get("/devices/{device_id}", response_model=DeviceResponse)
async def get_device(
    device_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(check_permissions(["network:read"]))
) -> Any:
    """Get specific device details"""
    try:
        device = await network_service.get_device(db, device_id, current_user.id)
        if not device:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Device not found"
            )
        return device
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get device {device_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve device"
        )


@router.put("/devices/{device_id}", response_model=DeviceResponse)
async def update_device(
    device_id: int,
    device_update: DeviceUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(check_permissions(["network:write"]))
) -> Any:
    """Update device configuration"""
    try:
        device = await network_service.update_device(db, device_id, device_update, current_user.id)
        if not device:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Device not found"
            )
        logger.info(f"Device {device_id} updated by user {current_user.username}")
        return device
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update device {device_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.delete("/devices/{device_id}")
async def delete_device(
    device_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(check_permissions(["network:delete"]))
) -> Any:
    """Remove device from monitoring"""
    try:
        success = await network_service.delete_device(db, device_id, current_user.id)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Device not found"
            )
        logger.info(f"Device {device_id} deleted by user {current_user.username}")
        return {"message": "Device deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete device {device_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.post("/scan")
async def scan_network(
    scan_request: NetworkScanRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(check_permissions(["network:scan"]))
) -> Any:
    """Scan network for discoverable devices"""
    try:
        result = await network_service.scan_network(db, scan_request, current_user.id)
        logger.info(f"Network scan initiated by user {current_user.username}")
        return result
    except Exception as e:
        logger.error(f"Failed to scan network: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.get("/topology", response_model=NetworkTopologyResponse)
async def get_network_topology(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(check_permissions(["network:read"]))
) -> Any:
    """Get network topology visualization data"""
    try:
        topology = await network_service.get_network_topology(db, current_user.id)
        return topology
    except Exception as e:
        logger.error(f"Failed to get network topology: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve network topology"
        )


@router.get("/metrics", response_model=NetworkMetricsResponse)
async def get_network_metrics(
    device_id: Optional[int] = None,
    time_range: str = "1h",
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(check_permissions(["network:read"]))
) -> Any:
    """Get network performance metrics"""
    try:
        metrics = await network_service.get_network_metrics(db, device_id, time_range, current_user.id)
        return metrics
    except Exception as e:
        logger.error(f"Failed to get network metrics: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve network metrics"
        )


@router.post("/devices/{device_id}/snmp-config")
async def configure_snmp(
    device_id: int,
    snmp_config: SNMPConfig,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(check_permissions(["network:write"]))
) -> Any:
    """Configure SNMP settings for a device"""
    try:
        result = await network_service.configure_snmp(db, device_id, snmp_config, current_user.id)
        logger.info(f"SNMP configured for device {device_id} by user {current_user.username}")
        return result
    except Exception as e:
        logger.error(f"Failed to configure SNMP for device {device_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.websocket("/realtime")
async def websocket_network_monitoring(
    websocket: WebSocket,
    token: str = None
):
    """Real-time network monitoring via WebSocket"""
    await websocket.accept()
    
    try:
        # Authenticate WebSocket connection
        if token:
            # Verify token and get user
            from app.core.security import verify_token
            payload = verify_token(token)
            username = payload.get("sub")
            logger.info(f"WebSocket connection established for user: {username}")
        else:
            await websocket.close(code=4001, reason="Authentication required")
            return
        
        # Start real-time monitoring
        while True:
            try:
                # Get real-time network data
                data = await network_service.get_realtime_data()
                await websocket.send_json(data)
                await asyncio.sleep(5)  # Send updates every 5 seconds
            except Exception as e:
                logger.error(f"Error sending WebSocket data: {e}")
                await websocket.send_json({"error": str(e)})
                break
                
    except WebSocketDisconnect:
        logger.info("WebSocket client disconnected")
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        await websocket.close(code=4000, reason="Internal server error")
