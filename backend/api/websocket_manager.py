import json
import asyncio
import logging
from typing import List, Dict, Any
from fastapi import WebSocket, WebSocketDisconnect
from datetime import datetime

class WebSocketManager:
    """
    Manages WebSocket connections for real-time updates
    Handles broadcasting to all connected clients
    """
    
    def __init__(self):
        self.active_connections: List[WebSocket] = []
        self.logger = logging.getLogger("websocket_manager")
        
        # Connection metadata
        self.connection_metadata: Dict[WebSocket, Dict[str, Any]] = {}
    
    async def connect(self, websocket: WebSocket):
        """Accept a new WebSocket connection"""
        await websocket.accept()
        self.active_connections.append(websocket)
        
        # Store connection metadata
        self.connection_metadata[websocket] = {
            'connected_at': datetime.utcnow(),
            'last_ping': datetime.utcnow(),
            'client_info': {}
        }
        
        self.logger.info(f"WebSocket connected. Total connections: {len(self.active_connections)}")
        
        # Send welcome message
        await self.send_to_connection(websocket, {
            'type': 'connection_established',
            'message': 'Connected to Dreamcatcher',
            'timestamp': datetime.utcnow().isoformat()
        })
    
    def disconnect(self, websocket: WebSocket):
        """Remove a WebSocket connection"""
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
            
        if websocket in self.connection_metadata:
            del self.connection_metadata[websocket]
            
        self.logger.info(f"WebSocket disconnected. Total connections: {len(self.active_connections)}")
    
    async def send_to_connection(self, websocket: WebSocket, data: Dict[str, Any]):
        """Send data to a specific connection"""
        try:
            await websocket.send_text(json.dumps(data, default=str))
        except Exception as e:
            self.logger.error(f"Failed to send message to connection: {e}")
            self.disconnect(websocket)
    
    async def broadcast(self, data: Dict[str, Any]):
        """Broadcast data to all connected clients"""
        if not self.active_connections:
            return
        
        # Add timestamp if not present
        if 'timestamp' not in data:
            data['timestamp'] = datetime.utcnow().isoformat()
        
        message = json.dumps(data, default=str)
        
        # Send to all connections
        disconnected_connections = []
        
        for connection in self.active_connections:
            try:
                await connection.send_text(message)
            except Exception as e:
                self.logger.error(f"Failed to broadcast to connection: {e}")
                disconnected_connections.append(connection)
        
        # Clean up failed connections
        for connection in disconnected_connections:
            self.disconnect(connection)
        
        self.logger.debug(f"Broadcast message to {len(self.active_connections)} connections")
    
    async def broadcast_to_filtered(self, data: Dict[str, Any], filter_func=None):
        """Broadcast to connections matching a filter"""
        if not self.active_connections:
            return
        
        # Add timestamp if not present
        if 'timestamp' not in data:
            data['timestamp'] = datetime.utcnow().isoformat()
        
        message = json.dumps(data, default=str)
        
        # Send to filtered connections
        disconnected_connections = []
        sent_count = 0
        
        for connection in self.active_connections:
            try:
                # Apply filter if provided
                if filter_func and not filter_func(connection, self.connection_metadata.get(connection, {})):
                    continue
                
                await connection.send_text(message)
                sent_count += 1
                
            except Exception as e:
                self.logger.error(f"Failed to broadcast to filtered connection: {e}")
                disconnected_connections.append(connection)
        
        # Clean up failed connections
        for connection in disconnected_connections:
            self.disconnect(connection)
        
        self.logger.debug(f"Broadcast filtered message to {sent_count} connections")
    
    async def notify_idea_captured(self, idea_id: str, source: str, content: str):
        """Notify all clients of a new idea capture"""
        await self.broadcast({
            'type': 'idea_captured',
            'idea_id': idea_id,
            'source': source,
            'content': content[:100] + '...' if len(content) > 100 else content,
            'full_content': content
        })
    
    async def notify_proposal_generated(self, proposal_id: str, idea_id: str, title: str):
        """Notify all clients of a new proposal"""
        await self.broadcast({
            'type': 'proposal_generated',
            'proposal_id': proposal_id,
            'idea_id': idea_id,
            'title': title
        })
    
    async def notify_agent_status(self, agent_id: str, status: str, message: str):
        """Notify all clients of agent status changes"""
        await self.broadcast({
            'type': 'agent_status',
            'agent_id': agent_id,
            'status': status,
            'message': message
        })
    
    async def notify_visual_generated(self, idea_id: str, visual_id: str, image_path: str):
        """Notify all clients of a new visual generation"""
        await self.broadcast({
            'type': 'visual_generated',
            'idea_id': idea_id,
            'visual_id': visual_id,
            'image_path': image_path
        })
    
    async def notify_system_alert(self, alert_type: str, message: str, severity: str = 'info'):
        """Notify all clients of system alerts"""
        await self.broadcast({
            'type': 'system_alert',
            'alert_type': alert_type,
            'message': message,
            'severity': severity
        })
    
    async def ping_all_connections(self):
        """Send ping to all connections to keep them alive"""
        if not self.active_connections:
            return
        
        ping_data = {
            'type': 'ping',
            'timestamp': datetime.utcnow().isoformat()
        }
        
        disconnected_connections = []
        
        for connection in self.active_connections:
            try:
                await connection.send_text(json.dumps(ping_data, default=str))
                
                # Update last ping time
                if connection in self.connection_metadata:
                    self.connection_metadata[connection]['last_ping'] = datetime.utcnow()
                    
            except Exception as e:
                self.logger.error(f"Failed to ping connection: {e}")
                disconnected_connections.append(connection)
        
        # Clean up failed connections
        for connection in disconnected_connections:
            self.disconnect(connection)
    
    def get_connection_count(self) -> int:
        """Get the number of active connections"""
        return len(self.active_connections)
    
    def get_connection_stats(self) -> Dict[str, Any]:
        """Get statistics about connections"""
        if not self.active_connections:
            return {
                'total_connections': 0,
                'oldest_connection': None,
                'newest_connection': None
            }
        
        connection_times = [
            meta['connected_at'] 
            for meta in self.connection_metadata.values()
        ]
        
        return {
            'total_connections': len(self.active_connections),
            'oldest_connection': min(connection_times).isoformat(),
            'newest_connection': max(connection_times).isoformat(),
            'connections_metadata': [
                {
                    'connected_at': meta['connected_at'].isoformat(),
                    'last_ping': meta['last_ping'].isoformat(),
                    'client_info': meta.get('client_info', {})
                }
                for meta in self.connection_metadata.values()
            ]
        }
    
    async def cleanup_stale_connections(self, timeout_minutes: int = 30):
        """Clean up connections that haven't pinged recently"""
        if not self.active_connections:
            return
        
        current_time = datetime.utcnow()
        stale_connections = []
        
        for connection, metadata in self.connection_metadata.items():
            last_ping = metadata.get('last_ping', metadata['connected_at'])
            minutes_since_ping = (current_time - last_ping).total_seconds() / 60
            
            if minutes_since_ping > timeout_minutes:
                stale_connections.append(connection)
        
        # Remove stale connections
        for connection in stale_connections:
            self.logger.info(f"Removing stale connection (inactive for {timeout_minutes} minutes)")
            self.disconnect(connection)
        
        return len(stale_connections)

# Global WebSocket manager instance
websocket_manager = WebSocketManager()