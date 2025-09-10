from fastapi import WebSocket
from typing import List, Dict, Set
import json
import asyncio
import logging
from datetime import datetime

logger = logging.getLogger(__name__)


class WebSocketManager:
    """Manages WebSocket connections and broadcasting"""
    
    def __init__(self):
        # Active connections per channel
        self.active_connections: Dict[str, Set[WebSocket]] = {
            "vulnerabilities": set(),
            "alerts": set(),
            "dashboard": set()
        }
        
        # Connection metadata
        self.connection_metadata: Dict[WebSocket, Dict] = {}
        
        # Subscription filters per connection
        self.connection_filters: Dict[WebSocket, Dict] = {}
    
    async def startup(self):
        """Initialize WebSocket manager"""
        logger.info("WebSocket manager started")
    
    async def shutdown(self):
        """Shutdown WebSocket manager"""
        logger.info("WebSocket manager shutting down")
        # Close all connections
        for channel_connections in self.active_connections.values():
            for connection in channel_connections.copy():
                try:
                    await connection.close()
                except:
                    pass
    
    async def connect(self, websocket: WebSocket, channel: str = "vulnerabilities"):
        """Accept a WebSocket connection"""
        await websocket.accept()
        
        if channel not in self.active_connections:
            self.active_connections[channel] = set()
        
        self.active_connections[channel].add(websocket)
        
        # Store connection metadata
        self.connection_metadata[websocket] = {
            "channel": channel,
            "connected_at": datetime.utcnow(),
            "last_seen": datetime.utcnow()
        }
        
        logger.info(f"WebSocket connected to channel '{channel}'. Total connections: {self.get_connection_count()}")
    
    def disconnect(self, websocket: WebSocket, channel: str = None):
        """Remove a WebSocket connection"""
        # If channel not specified, find it from metadata
        if not channel and websocket in self.connection_metadata:
            channel = self.connection_metadata[websocket]["channel"]
        
        # Remove from active connections
        if channel and channel in self.active_connections:
            self.active_connections[channel].discard(websocket)
        
        # Clean up metadata
        self.connection_metadata.pop(websocket, None)
        self.connection_filters.pop(websocket, None)
        
        logger.info(f"WebSocket disconnected from channel '{channel}'. Total connections: {self.get_connection_count()}")
    
    async def send_personal_message(self, message: dict, websocket: WebSocket):
        """Send a message to a specific WebSocket connection"""
        try:
            await websocket.send_json(message)
        except Exception as e:
            logger.error(f"Error sending personal message: {e}")
            # Remove broken connection
            for channel, connections in self.active_connections.items():
                if websocket in connections:
                    self.disconnect(websocket, channel)
                    break
    
    async def broadcast_to_channel(self, message: dict, channel: str):
        """Broadcast a message to all connections in a channel"""
        if channel not in self.active_connections:
            return
        
        connections = self.active_connections[channel].copy()
        disconnected = []
        
        for connection in connections:
            try:
                # Apply filters if they exist
                if self._should_send_message(connection, message):
                    await connection.send_json(message)
            except Exception as e:
                logger.error(f"Error broadcasting to connection: {e}")
                disconnected.append(connection)
        
        # Clean up disconnected connections
        for connection in disconnected:
            self.disconnect(connection, channel)
    
    async def broadcast_vulnerability_update(self, vulnerability_data: dict):
        """Broadcast vulnerability update to subscribers"""
        message = {
            "type": "vulnerability_update",
            "timestamp": datetime.utcnow().isoformat(),
            "data": vulnerability_data
        }
        
        await self.broadcast_to_channel(message, "vulnerabilities")
        
        # Also send to dashboard if it's a critical vulnerability
        if vulnerability_data.get("severity") == "CRITICAL":
            dashboard_message = {
                "type": "critical_vulnerability",
                "timestamp": datetime.utcnow().isoformat(),
                "data": vulnerability_data
            }
            await self.broadcast_to_channel(dashboard_message, "dashboard")
    
    async def broadcast_alert_notification(self, alert_data: dict):
        """Broadcast alert notification to subscribers"""
        message = {
            "type": "alert_notification",
            "timestamp": datetime.utcnow().isoformat(),
            "data": alert_data
        }
        
        await self.broadcast_to_channel(message, "alerts")
        await self.broadcast_to_channel(message, "dashboard")
    
    async def update_subscription(self, websocket: WebSocket, filters: dict):
        """Update subscription filters for a connection"""
        self.connection_filters[websocket] = filters
        logger.info(f"Updated subscription filters for connection: {filters}")
    
    def _should_send_message(self, websocket: WebSocket, message: dict) -> bool:
        """Check if message should be sent based on connection filters"""
        filters = self.connection_filters.get(websocket, {})
        
        if not filters:
            return True  # No filters, send everything
        
        message_data = message.get("data", {})
        
        # Check severity filter
        if "severity" in filters:
            if message_data.get("severity") != filters["severity"]:
                return False
        
        # Check tool filter
        if "tool" in filters:
            affected_tools = message_data.get("affected_tools", [])
            if filters["tool"] not in affected_tools:
                return False
        
        # Check priority filter for alerts
        if "priority" in filters:
            if message_data.get("priority") != filters["priority"]:
                return False
        
        return True
    
    def get_connection_count(self, channel: str = None) -> int:
        """Get total connection count or count for specific channel"""
        if channel:
            return len(self.active_connections.get(channel, set()))
        
        return sum(len(connections) for connections in self.active_connections.values())
    
    def get_connection_stats(self) -> dict:
        """Get detailed connection statistics"""
        stats = {
            "total_connections": self.get_connection_count(),
            "channels": {}
        }
        
        for channel, connections in self.active_connections.items():
            stats["channels"][channel] = len(connections)
        
        return stats
    
    async def send_heartbeat(self):
        """Send heartbeat to all connections"""
        heartbeat_message = {
            "type": "heartbeat",
            "timestamp": datetime.utcnow().isoformat()
        }
        
        for channel in self.active_connections:
            await self.broadcast_to_channel(heartbeat_message, channel)
    
    async def start_heartbeat_task(self, interval: int = 30):
        """Start periodic heartbeat task"""
        async def heartbeat_loop():
            while True:
                await asyncio.sleep(interval)
                await self.send_heartbeat()
        
        # Start heartbeat task
        asyncio.create_task(heartbeat_loop())


# Global WebSocket manager instance
websocket_manager = WebSocketManager()