from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query
from typing import Optional
import json
import logging

from app.services.websocket_manager import websocket_manager
from app.models.vulnerability import SeverityEnum

router = APIRouter()
logger = logging.getLogger(__name__)


@router.websocket("/vulnerabilities")
async def vulnerability_websocket(
    websocket: WebSocket,
    severity: Optional[str] = Query(None, description="Filter by severity"),
    tool: Optional[str] = Query(None, description="Filter by AI tool")
):
    """WebSocket endpoint for real-time vulnerability updates"""
    
    await websocket_manager.connect(websocket)
    
    # Send connection confirmation
    await websocket.send_json({
        "type": "connection",
        "status": "connected",
        "message": "Connected to vulnerability updates"
    })
    
    try:
        while True:
            # Wait for client messages (ping, filters, etc.)
            try:
                data = await websocket.receive_json()
                
                if data.get("type") == "ping":
                    await websocket.send_json({
                        "type": "pong",
                        "timestamp": data.get("timestamp")
                    })
                
                elif data.get("type") == "subscribe":
                    # Update subscription filters
                    filters = data.get("filters", {})
                    await websocket_manager.update_subscription(websocket, filters)
                    await websocket.send_json({
                        "type": "subscription_updated",
                        "filters": filters
                    })
                    
            except Exception as e:
                logger.error(f"Error handling websocket message: {e}")
                continue
                
    except WebSocketDisconnect:
        logger.info("WebSocket client disconnected")
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
    finally:
        websocket_manager.disconnect(websocket)


@router.websocket("/alerts")
async def alert_websocket(
    websocket: WebSocket,
    priority: Optional[str] = Query(None, description="Filter by priority")
):
    """WebSocket endpoint for real-time alert notifications"""
    
    await websocket_manager.connect(websocket, channel="alerts")
    
    await websocket.send_json({
        "type": "connection",
        "status": "connected", 
        "channel": "alerts",
        "message": "Connected to alert notifications"
    })
    
    try:
        while True:
            try:
                data = await websocket.receive_json()
                
                if data.get("type") == "ping":
                    await websocket.send_json({
                        "type": "pong",
                        "timestamp": data.get("timestamp")
                    })
                    
            except Exception as e:
                logger.error(f"Error handling alert websocket message: {e}")
                continue
                
    except WebSocketDisconnect:
        logger.info("Alert WebSocket client disconnected")
    except Exception as e:
        logger.error(f"Alert WebSocket error: {e}")
    finally:
        websocket_manager.disconnect(websocket, channel="alerts")


@router.websocket("/dashboard")
async def dashboard_websocket(websocket: WebSocket):
    """WebSocket endpoint for dashboard real-time updates"""
    
    await websocket_manager.connect(websocket, channel="dashboard")
    
    await websocket.send_json({
        "type": "connection",
        "status": "connected",
        "channel": "dashboard",
        "message": "Connected to dashboard updates"
    })
    
    try:
        while True:
            try:
                data = await websocket.receive_json()
                
                if data.get("type") == "ping":
                    await websocket.send_json({
                        "type": "pong",
                        "timestamp": data.get("timestamp")
                    })
                elif data.get("type") == "get_stats":
                    # Send current statistics
                    # TODO: Implement real-time stats
                    await websocket.send_json({
                        "type": "stats",
                        "data": {
                            "total_vulnerabilities": 0,
                            "active_alerts": 0,
                            "connected_clients": websocket_manager.get_connection_count()
                        }
                    })
                    
            except Exception as e:
                logger.error(f"Error handling dashboard websocket message: {e}")
                continue
                
    except WebSocketDisconnect:
        logger.info("Dashboard WebSocket client disconnected")
    except Exception as e:
        logger.error(f"Dashboard WebSocket error: {e}")
    finally:
        websocket_manager.disconnect(websocket, channel="dashboard")