"""
WebSocket Router for Real-Time Updates
Provides live AQI updates to connected clients
"""

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
import asyncio
import json
from datetime import datetime
from typing import Dict, Set
import logging

from app.database import async_session_maker
from app.models import Location, AQIReading, Prediction

router = APIRouter(tags=["websocket"])
logger = logging.getLogger(__name__)


class ConnectionManager:
    """
    Manages WebSocket connections for real-time updates.
    Supports multiple clients per location.
    """
    
    def __init__(self):
        # location_id -> set of connected websockets
        self.active_connections: Dict[int, Set[WebSocket]] = {}
        self._broadcast_task = None
    
    async def connect(self, websocket: WebSocket, location_id: int):
        """Accept a new WebSocket connection"""
        await websocket.accept()
        
        if location_id not in self.active_connections:
            self.active_connections[location_id] = set()
        
        self.active_connections[location_id].add(websocket)
        logger.info(f"Client connected for location {location_id}")
    
    def disconnect(self, websocket: WebSocket, location_id: int):
        """Remove a WebSocket connection"""
        if location_id in self.active_connections:
            self.active_connections[location_id].discard(websocket)
            
            # Clean up empty sets
            if not self.active_connections[location_id]:
                del self.active_connections[location_id]
        
        logger.info(f"Client disconnected from location {location_id}")
    
    async def send_personal_message(self, message: dict, websocket: WebSocket):
        """Send a message to a specific client"""
        try:
            await websocket.send_json(message)
        except Exception as e:
            logger.error(f"Failed to send message: {e}")
    
    async def broadcast_to_location(self, message: dict, location_id: int):
        """Broadcast a message to all clients watching a location"""
        if location_id not in self.active_connections:
            return
        
        disconnected = set()
        
        for websocket in self.active_connections[location_id]:
            try:
                await websocket.send_json(message)
            except Exception as e:
                logger.warning(f"Failed to broadcast to client: {e}")
                disconnected.add(websocket)
        
        # Clean up disconnected clients
        for ws in disconnected:
            self.active_connections[location_id].discard(ws)
    
    async def broadcast_to_all(self, message: dict):
        """Broadcast a message to all connected clients"""
        for location_id in list(self.active_connections.keys()):
            await self.broadcast_to_location(message, location_id)
    
    def get_connection_count(self, location_id: int = None) -> int:
        """Get number of active connections"""
        if location_id is not None:
            return len(self.active_connections.get(location_id, set()))
        return sum(len(conns) for conns in self.active_connections.values())


# Global connection manager
manager = ConnectionManager()


async def get_latest_data(location_id: int) -> dict:
    """Fetch latest AQI data and predictions for a location"""
    async with async_session_maker() as session:
        # Get location
        result = await session.execute(
            select(Location).where(Location.id == location_id)
        )
        location = result.scalar_one_or_none()
        
        if not location:
            return {"error": f"Location {location_id} not found"}
        
        # Get latest reading
        result = await session.execute(
            select(AQIReading)
            .where(AQIReading.location_id == location_id)
            .order_by(desc(AQIReading.recorded_at))
            .limit(1)
        )
        reading = result.scalar_one_or_none()
        
        # Get latest predictions
        now = datetime.now()
        result = await session.execute(
            select(Prediction)
            .where(
                Prediction.location_id == location_id,
                Prediction.prediction_for >= now
            )
            .order_by(Prediction.prediction_for)
            .limit(6)  # Next 6 hours
        )
        predictions = result.scalars().all()
        
        return {
            "type": "update",
            "location": {
                "id": location.id,
                "city": location.city,
                "country": location.country,
                "latitude": location.latitude,
                "longitude": location.longitude
            },
            "current": {
                "aqi_value": reading.aqi_value if reading else None,
                "aqi_category": reading.aqi_category if reading else None,
                "pm25": reading.pm25 if reading else None,
                "pm10": reading.pm10 if reading else None,
                "o3": reading.o3 if reading else None,
                "no2": reading.no2 if reading else None,
                "so2": reading.so2 if reading else None,
                "co": reading.co if reading else None,
                "recorded_at": reading.recorded_at.isoformat() if reading else None
            } if reading else None,
            "predictions": [
                {
                    "predicted_aqi": p.predicted_aqi,
                    "predicted_category": p.predicted_category,
                    "confidence": p.confidence,
                    "prediction_for": p.prediction_for.isoformat()
                }
                for p in predictions
            ],
            "timestamp": datetime.now().isoformat(),
            "connected_clients": manager.get_connection_count(location_id)
        }


@router.websocket("/ws/aqi/{location_id}")
async def websocket_aqi(websocket: WebSocket, location_id: int):
    """
    WebSocket endpoint for real-time AQI updates.
    
    Clients connect to /ws/aqi/{location_id} to receive:
    - Initial current data
    - Periodic updates (every 30 seconds)
    - Immediate updates when new data is available
    
    Messages:
    - type: "update" - Full data update
    - type: "ping" - Keep-alive ping
    - type: "error" - Error message
    """
    await manager.connect(websocket, location_id)
    
    try:
        # Send initial data
        initial_data = await get_latest_data(location_id)
        await manager.send_personal_message(initial_data, websocket)
        
        # Start periodic updates
        update_interval = 30  # seconds
        ping_interval = 15  # seconds
        
        last_update = datetime.now()
        last_ping = datetime.now()
        
        while True:
            try:
                # Check for client messages (non-blocking with timeout)
                try:
                    message = await asyncio.wait_for(
                        websocket.receive_text(),
                        timeout=1.0
                    )
                    
                    # Handle client messages
                    data = json.loads(message)
                    
                    if data.get("type") == "ping":
                        await manager.send_personal_message(
                            {"type": "pong", "timestamp": datetime.now().isoformat()},
                            websocket
                        )
                    elif data.get("type") == "refresh":
                        # Client requests immediate refresh
                        update_data = await get_latest_data(location_id)
                        await manager.send_personal_message(update_data, websocket)
                        last_update = datetime.now()
                        
                except asyncio.TimeoutError:
                    pass  # No message received, continue
                
                # Send periodic updates
                now = datetime.now()
                
                if (now - last_update).total_seconds() >= update_interval:
                    update_data = await get_latest_data(location_id)
                    await manager.send_personal_message(update_data, websocket)
                    last_update = now
                
                # Send ping to keep connection alive
                if (now - last_ping).total_seconds() >= ping_interval:
                    await manager.send_personal_message(
                        {"type": "ping", "timestamp": now.isoformat()},
                        websocket
                    )
                    last_ping = now
                    
            except WebSocketDisconnect:
                break
            except Exception as e:
                logger.error(f"WebSocket error: {e}")
                await manager.send_personal_message(
                    {"type": "error", "message": str(e)},
                    websocket
                )
                break
                
    except WebSocketDisconnect:
        pass
    finally:
        manager.disconnect(websocket, location_id)


@router.websocket("/ws/all")
async def websocket_all_locations(websocket: WebSocket):
    """
    WebSocket endpoint for updates from all locations.
    
    Useful for dashboard showing multiple locations.
    """
    await websocket.accept()
    
    try:
        while True:
            try:
                # Get all locations
                async with async_session_maker() as session:
                    result = await session.execute(select(Location))
                    locations = result.scalars().all()
                    
                    all_data = []
                    for location in locations:
                        data = await get_latest_data(location.id)
                        if "error" not in data:
                            all_data.append(data)
                    
                    await websocket.send_json({
                        "type": "all_locations",
                        "locations": all_data,
                        "timestamp": datetime.now().isoformat()
                    })
                
                await asyncio.sleep(30)  # Update every 30 seconds
                
            except WebSocketDisconnect:
                break
            except Exception as e:
                logger.error(f"WebSocket error: {e}")
                break
                
    except WebSocketDisconnect:
        pass
