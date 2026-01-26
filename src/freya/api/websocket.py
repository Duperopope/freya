# src/freya/api/websocket.py
"""
WebSocket Manager for Freya Real-Time Updates

Handles real-time communication for:
- Benchmark progress updates
- Chat streaming responses
- BMAD workflow progress
- System status updates
- Log streaming
"""

from __future__ import annotations

import asyncio
import json
import logging
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Callable, Coroutine
from weakref import WeakSet

from fastapi import WebSocket, WebSocketDisconnect

logger = logging.getLogger("freya.api.websocket")


class ChannelType(str, Enum):
    """WebSocket channel types for different update streams."""
    BENCH = "bench"           # Benchmark progress
    CHAT = "chat"             # Chat streaming
    BMAD = "bmad"             # BMAD workflow progress
    SYSTEM = "system"         # System status (CPU, RAM, etc.)
    LOGS = "logs"             # Log streaming
    FILES = "files"           # File system changes


@dataclass
class WSMessage:
    """Structured WebSocket message."""
    channel: ChannelType
    event: str
    data: dict[str, Any]
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    
    def to_json(self) -> str:
        return json.dumps({
            "channel": self.channel.value,
            "event": self.event,
            "data": self.data,
            "timestamp": self.timestamp,
        })


class WebSocketManager:
    """
    Manages WebSocket connections and broadcasts.
    
    Features:
    - Connection tracking by channel
    - Broadcast to all or specific channels
    - Automatic cleanup of dead connections
    - Thread-safe for background task integration
    """
    
    def __init__(self) -> None:
        # Connections by channel
        self._connections: dict[ChannelType, set[WebSocket]] = {
            channel: set() for channel in ChannelType
        }
        # All active connections
        self._all_connections: set[WebSocket] = set()
        # Lock for thread safety
        self._lock = asyncio.Lock()
        # Background tasks
        self._tasks: set[asyncio.Task] = set()
        # Shutdown flag
        self._shutdown = False
    
    async def connect(
        self,
        websocket: WebSocket,
        channels: list[ChannelType] | None = None
    ) -> None:
        """
        Accept and register a WebSocket connection.
        
        Args:
            websocket: The WebSocket to register
            channels: Channels to subscribe to (all if None)
        """
        await websocket.accept()
        
        async with self._lock:
            self._all_connections.add(websocket)
            
            # Subscribe to specified channels or all
            subscribe_channels = channels or list(ChannelType)
            for channel in subscribe_channels:
                self._connections[channel].add(websocket)
        
        logger.info(f"WebSocket connected, subscribed to: {[c.value for c in subscribe_channels]}")
        
        # Send welcome message
        await self.send_personal(websocket, WSMessage(
            channel=ChannelType.SYSTEM,
            event="connected",
            data={"subscribed": [c.value for c in subscribe_channels]}
        ))
    
    async def disconnect(self, websocket: WebSocket) -> None:
        """Remove a WebSocket from all channels."""
        async with self._lock:
            self._all_connections.discard(websocket)
            for channel in ChannelType:
                self._connections[channel].discard(websocket)
        
        logger.info("WebSocket disconnected")
    
    async def subscribe(self, websocket: WebSocket, channel: ChannelType) -> None:
        """Subscribe a WebSocket to a channel."""
        async with self._lock:
            self._connections[channel].add(websocket)
    
    async def unsubscribe(self, websocket: WebSocket, channel: ChannelType) -> None:
        """Unsubscribe a WebSocket from a channel."""
        async with self._lock:
            self._connections[channel].discard(websocket)
    
    async def send_personal(self, websocket: WebSocket, message: WSMessage) -> bool:
        """Send a message to a specific WebSocket."""
        try:
            await websocket.send_text(message.to_json())
            return True
        except Exception as e:
            logger.warning(f"Failed to send to WebSocket: {e}")
            await self.disconnect(websocket)
            return False
    
    async def broadcast(self, message: WSMessage) -> int:
        """
        Broadcast a message to all connections subscribed to the channel.
        
        Returns:
            Number of successful sends
        """
        async with self._lock:
            connections = list(self._connections[message.channel])
        
        if not connections:
            return 0
        
        sent = 0
        dead_connections = []
        
        for ws in connections:
            try:
                await ws.send_text(message.to_json())
                sent += 1
            except Exception:
                dead_connections.append(ws)
        
        # Clean up dead connections
        for ws in dead_connections:
            await self.disconnect(ws)
        
        return sent
    
    async def broadcast_all(self, message: WSMessage) -> int:
        """Broadcast to ALL connections regardless of channel."""
        async with self._lock:
            connections = list(self._all_connections)
        
        sent = 0
        dead_connections = []
        
        for ws in connections:
            try:
                await ws.send_text(message.to_json())
                sent += 1
            except Exception:
                dead_connections.append(ws)
        
        for ws in dead_connections:
            await self.disconnect(ws)
        
        return sent
    
    def broadcast_sync(self, message: WSMessage) -> None:
        """
        Thread-safe broadcast for use from synchronous code.
        Creates an asyncio task to perform the broadcast.
        """
        if self._shutdown:
            return
        
        try:
            loop = asyncio.get_running_loop()
            task = loop.create_task(self.broadcast(message))
            self._tasks.add(task)
            task.add_done_callback(self._tasks.discard)
        except RuntimeError:
            # No running event loop
            pass
    
    def create_progress_callback(self, channel: ChannelType) -> Callable[[str, dict], None]:
        """
        Create a progress callback for background operations.
        
        Returns a function that can be called from sync code to broadcast progress.
        """
        def callback(event: str, payload: dict[str, Any]) -> None:
            self.broadcast_sync(WSMessage(
                channel=channel,
                event=event,
                data=payload
            ))
        return callback
    
    async def shutdown(self) -> None:
        """Gracefully shutdown all connections."""
        self._shutdown = True
        
        # Wait for pending tasks
        if self._tasks:
            await asyncio.gather(*self._tasks, return_exceptions=True)
        
        # Close all connections
        async with self._lock:
            for ws in list(self._all_connections):
                try:
                    await ws.close()
                except Exception:
                    pass
            self._all_connections.clear()
            for channel in ChannelType:
                self._connections[channel].clear()
        
        logger.info("WebSocket manager shutdown complete")
    
    @property
    def connection_count(self) -> int:
        """Total number of active connections."""
        return len(self._all_connections)
    
    def channel_count(self, channel: ChannelType) -> int:
        """Number of connections subscribed to a channel."""
        return len(self._connections[channel])


# -----------------------------------------------------------------------------
# WebSocket Route Handler
# -----------------------------------------------------------------------------
async def websocket_endpoint(websocket: WebSocket, manager: WebSocketManager):
    """
    Main WebSocket endpoint handler.
    
    Protocol:
    - Connect and receive welcome message
    - Send JSON messages to subscribe/unsubscribe from channels
    - Receive broadcast messages for subscribed channels
    
    Client message format:
        {"action": "subscribe", "channel": "bench"}
        {"action": "unsubscribe", "channel": "logs"}
        {"action": "ping"}
    """
    await manager.connect(websocket)
    
    try:
        while True:
            try:
                data = await websocket.receive_text()
                msg = json.loads(data)
                action = msg.get("action", "")
                
                if action == "subscribe":
                    channel_name = msg.get("channel", "")
                    try:
                        channel = ChannelType(channel_name)
                        await manager.subscribe(websocket, channel)
                        await manager.send_personal(websocket, WSMessage(
                            channel=ChannelType.SYSTEM,
                            event="subscribed",
                            data={"channel": channel_name}
                        ))
                    except ValueError:
                        await manager.send_personal(websocket, WSMessage(
                            channel=ChannelType.SYSTEM,
                            event="error",
                            data={"message": f"Unknown channel: {channel_name}"}
                        ))
                
                elif action == "unsubscribe":
                    channel_name = msg.get("channel", "")
                    try:
                        channel = ChannelType(channel_name)
                        await manager.unsubscribe(websocket, channel)
                        await manager.send_personal(websocket, WSMessage(
                            channel=ChannelType.SYSTEM,
                            event="unsubscribed",
                            data={"channel": channel_name}
                        ))
                    except ValueError:
                        pass
                
                elif action == "ping":
                    await manager.send_personal(websocket, WSMessage(
                        channel=ChannelType.SYSTEM,
                        event="pong",
                        data={}
                    ))
                
            except json.JSONDecodeError:
                await manager.send_personal(websocket, WSMessage(
                    channel=ChannelType.SYSTEM,
                    event="error",
                    data={"message": "Invalid JSON"}
                ))
    
    except WebSocketDisconnect:
        await manager.disconnect(websocket)
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        await manager.disconnect(websocket)
