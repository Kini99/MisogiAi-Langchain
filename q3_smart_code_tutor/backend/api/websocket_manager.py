"""
WebSocket connection manager for handling multiple concurrent connections
"""
import asyncio
import json
import logging
from typing import Dict, Set
from fastapi import WebSocket

logger = logging.getLogger(__name__)


class WebSocketManager:
    """Manages WebSocket connections for real-time communication"""
    
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}
        self.connection_tasks: Dict[str, asyncio.Task] = {}
        self.max_connections = 100
        
    async def connect(self, websocket: WebSocket, client_id: str):
        """Connect a new WebSocket client"""
        if len(self.active_connections) >= self.max_connections:
            await websocket.close(code=1008, reason="Maximum connections reached")
            return
            
        await websocket.accept()
        self.active_connections[client_id] = websocket
        logger.info(f"Client {client_id} connected. Total connections: {len(self.active_connections)}")
        
    def disconnect(self, client_id: str):
        """Disconnect a WebSocket client"""
        if client_id in self.active_connections:
            del self.active_connections[client_id]
            
        if client_id in self.connection_tasks:
            task = self.connection_tasks[client_id]
            if not task.done():
                task.cancel()
            del self.connection_tasks[client_id]
            
        logger.info(f"Client {client_id} disconnected. Total connections: {len(self.active_connections)}")
        
    async def send_personal_message(self, message: str, client_id: str):
        """Send a message to a specific client"""
        if client_id in self.active_connections:
            try:
                await self.active_connections[client_id].send_text(message)
            except Exception as e:
                logger.error(f"Error sending message to client {client_id}: {e}")
                self.disconnect(client_id)
                
    async def broadcast(self, message: str, exclude_client: str = None):
        """Broadcast a message to all connected clients"""
        disconnected_clients = []
        
        for client_id, connection in self.active_connections.items():
            if client_id != exclude_client:
                try:
                    await connection.send_text(message)
                except Exception as e:
                    logger.error(f"Error broadcasting to client {client_id}: {e}")
                    disconnected_clients.append(client_id)
                    
        # Clean up disconnected clients
        for client_id in disconnected_clients:
            self.disconnect(client_id)
            
    async def send_json(self, data: dict, client_id: str):
        """Send JSON data to a specific client"""
        await self.send_personal_message(json.dumps(data), client_id)
        
    async def broadcast_json(self, data: dict, exclude_client: str = None):
        """Broadcast JSON data to all connected clients"""
        await self.broadcast(json.dumps(data), exclude_client)
        
    def get_connection_count(self) -> int:
        """Get the number of active connections"""
        return len(self.active_connections)
        
    def is_connected(self, client_id: str) -> bool:
        """Check if a client is connected"""
        return client_id in self.active_connections
        
    async def close_all_connections(self):
        """Close all active connections"""
        for client_id, connection in self.active_connections.items():
            try:
                await connection.close()
            except Exception as e:
                logger.error(f"Error closing connection for client {client_id}: {e}")
                
        self.active_connections.clear()
        self.connection_tasks.clear()
        logger.info("All WebSocket connections closed") 