import json
import logging
from typing import List, Dict
from fastapi import WebSocket
from datetime import datetime

logger = logging.getLogger(__name__)


class ConnectionManager:
    def __init__(self):
        """Initialize WebSocket connection manager"""
        self.active_connections: List[WebSocket] = []
        self.user_connections: Dict[int, WebSocket] = {}
        self.project_subscriptions: Dict[int, List[int]] = {}  # project_id -> [user_ids]
        logger.info("ConnectionManager initialized")
    
    async def connect(self, websocket: WebSocket, user_id: int):
        """Accept WebSocket connection and register user"""
        await websocket.accept()
        self.active_connections.append(websocket)
        self.user_connections[user_id] = websocket
        logger.info(f"User {user_id} connected via WebSocket")
    
    def disconnect(self, websocket: WebSocket, user_id: int):
        """Remove WebSocket connection"""
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
        if user_id in self.user_connections:
            del self.user_connections[user_id]
        
        # Remove from project subscriptions
        for project_id, subscribers in self.project_subscriptions.items():
            if user_id in subscribers:
                subscribers.remove(user_id)
        
        logger.info(f"User {user_id} disconnected from WebSocket")
    
    async def broadcast_allocation_update(self, allocation_update: Dict):
        """Broadcast allocation changes to all connected clients"""
        message = {
            "type": "allocation_update",
            "data": allocation_update,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        await self._broadcast_message(message)
    
    async def broadcast_employee_update(self, employee_update: Dict):
        """Broadcast employee updates to all connected clients"""
        message = {
            "type": "employee_update",
            "data": employee_update,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        await self._broadcast_message(message)
    
    async def broadcast_project_update(self, project_update: Dict):
        """Broadcast project updates to all connected clients"""
        message = {
            "type": "project_update",
            "data": project_update,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        await self._broadcast_message(message)
    
    async def broadcast_matching_update(self, matching_update: Dict):
        """Broadcast matching results to all connected clients"""
        message = {
            "type": "matching_update",
            "data": matching_update,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        await self._broadcast_message(message)
    
    async def send_conflict_alert(self, user_id: int, conflict_data: Dict):
        """Send conflict alert to specific user"""
        if user_id in self.user_connections:
            message = {
                "type": "conflict_alert",
                "data": conflict_data,
                "timestamp": datetime.utcnow().isoformat()
            }
            
            try:
                await self.user_connections[user_id].send_text(json.dumps(message))
            except Exception as e:
                logger.error(f"Failed to send conflict alert to user {user_id}: {str(e)}")
                # Remove broken connection
                if user_id in self.user_connections:
                    del self.user_connections[user_id]
    
    async def send_to_user(self, user_id: int, message: Dict):
        """Send message to specific user"""
        if user_id in self.user_connections:
            try:
                await self.user_connections[user_id].send_text(json.dumps(message))
            except Exception as e:
                logger.error(f"Failed to send message to user {user_id}: {str(e)}")
                # Remove broken connection
                if user_id in self.user_connections:
                    del self.user_connections[user_id]
    
    async def broadcast_to_project_subscribers(self, project_id: int, message: Dict):
        """Broadcast message to users subscribed to a specific project"""
        if project_id in self.project_subscriptions:
            for user_id in self.project_subscriptions[project_id]:
                await self.send_to_user(user_id, message)
    
    async def subscribe_to_project(self, user_id: int, project_id: int):
        """Subscribe user to project updates"""
        if project_id not in self.project_subscriptions:
            self.project_subscriptions[project_id] = []
        
        if user_id not in self.project_subscriptions[project_id]:
            self.project_subscriptions[project_id].append(user_id)
            logger.info(f"User {user_id} subscribed to project {project_id}")
    
    async def unsubscribe_from_project(self, user_id: int, project_id: int):
        """Unsubscribe user from project updates"""
        if project_id in self.project_subscriptions:
            if user_id in self.project_subscriptions[project_id]:
                self.project_subscriptions[project_id].remove(user_id)
                logger.info(f"User {user_id} unsubscribed from project {project_id}")
    
    async def _broadcast_message(self, message: Dict):
        """Broadcast message to all active connections"""
        disconnected = []
        
        for connection in self.active_connections:
            try:
                await connection.send_text(json.dumps(message))
            except Exception as e:
                logger.error(f"Failed to send message to connection: {str(e)}")
                disconnected.append(connection)
        
        # Clean up disconnected clients
        for conn in disconnected:
            if conn in self.active_connections:
                self.active_connections.remove(conn)
    
    def get_connection_stats(self) -> Dict:
        """Get connection statistics"""
        return {
            "active_connections": len(self.active_connections),
            "user_connections": len(self.user_connections),
            "project_subscriptions": len(self.project_subscriptions),
            "total_subscriptions": sum(len(subscribers) for subscribers in self.project_subscriptions.values())
        }
