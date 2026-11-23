"""
Real-time WebSocket Connection Manager for SkillSphere Support & Live Chat (Stage 7).

ARCHITECTURE & CONCURRENCY CONSTRAINTS:
- SINGLE-INSTANCE DEPLOYMENT ONLY: This in-memory connection manager is explicitly designed
  and constrained for single Render instance / single Uvicorn worker deployments.
- Horizontal scaling to multiple instances or workers requires an external message broker
  (e.g., Redis Pub/Sub, RabbitMQ, or NATS). In single-worker deployments, in-memory room tracking
  is deterministic, zero-dependency, and latency-free.
- SECURITY INVARIANT: Internal notes (is_internal=True) are strictly filtered out and NEVER
  broadcast to non-admin connections.
- AUTHENTICATION INVARIANT: Never authenticate WebSocket connections directly with long-lived JWTs
  in the URL query string. Handshakes must validate short-lived, single-use connection tickets
  issued by the authenticated REST endpoint POST /api/v1/tickets/{id}/ws-auth-ticket.
- PROTOCOL: Supports application-level JSON ping/pong for browser keep-alive heartbeats.
"""

import json
import logging
from typing import Dict, Any, Optional
from fastapi import WebSocket, WebSocketDisconnect

logger = logging.getLogger("skillsphere.websocket")


class ConnectionManager:
    def __init__(self):
        # ticket_id -> {connection_id: {"websocket": WebSocket, "user_id": str, "user_role": str, "user_name": str}}
        self.rooms: Dict[str, Dict[str, Dict[str, Any]]] = {}

    async def connect(self, ticket_id: str, connection_id: str, websocket: WebSocket, user_id: str, user_role: str, user_name: str):
        """Register a validated WebSocket connection to a ticket room."""
        await websocket.accept()
        if ticket_id not in self.rooms:
            self.rooms[ticket_id] = {}
        self.rooms[ticket_id][connection_id] = {
            "websocket": websocket,
            "user_id": user_id,
            "user_role": user_role,
            "user_name": user_name
        }
        logger.info(f"WebSocket connected: ticket={ticket_id}, user={user_id}, role={user_role}, conn_id={connection_id}")

        # Broadcast participant join notice to the room
        await self.broadcast_event(
            ticket_id=ticket_id,
            event_type="user_joined",
            data={
                "ticket_id": ticket_id,
                "user_id": user_id,
                "user_name": user_name,
                "user_role": user_role,
                "room_occupancy": len(self.rooms[ticket_id])
            },
            is_internal=False
        )

    def disconnect(self, ticket_id: str, connection_id: str):
        """Remove a disconnected WebSocket from the ticket room."""
        if ticket_id in self.rooms and connection_id in self.rooms[ticket_id]:
            user_info = self.rooms[ticket_id].pop(connection_id, None)
            if not self.rooms[ticket_id]:
                del self.rooms[ticket_id]
            logger.info(f"WebSocket disconnected: ticket={ticket_id}, conn_id={connection_id}")
            return user_info
        return None

    def get_room_occupancy(self, ticket_id: str) -> int:
        """Return the number of active connections in a ticket room."""
        return len(self.rooms.get(ticket_id, {}))

    def has_admin_in_room(self, ticket_id: str) -> bool:
        """Check if at least one ADMIN is actively connected to the ticket room."""
        room = self.rooms.get(ticket_id, {})
        return any(conn["user_role"] == "ADMIN" for conn in room.values())

    async def broadcast_event(self, ticket_id: str, event_type: str, data: Dict[str, Any], is_internal: bool = False):
        """
        Broadcast an event to all participants in a ticket room.
        CRITICAL PRIVACY INVARIANT:
        If is_internal is True, the payload is transmitted ONLY to ADMIN connections.
        Non-admins will NEVER receive internal note events.
        """
        room = self.rooms.get(ticket_id, {})
        if not room:
            return

        payload = {
            "type": event_type,
            "ticket_id": ticket_id,
            "data": data
        }
        serialized = json.dumps(payload, default=str)

        disconnected_conns = []
        for conn_id, conn in list(room.items()):
            # Security filter: Never leak internal events to non-admins
            if is_internal and conn["user_role"] != "ADMIN":
                continue

            try:
                await conn["websocket"].send_text(serialized)
            except Exception as e:
                logger.warning(f"Failed to send to conn {conn_id} in ticket {ticket_id}: {e}")
                disconnected_conns.append(conn_id)

        # Cleanup failed connections
        for conn_id in disconnected_conns:
            self.disconnect(ticket_id, conn_id)

    async def send_personal_message(self, websocket: WebSocket, event_type: str, data: Dict[str, Any]):
        """Send a direct event to a single WebSocket client."""
        payload = {
            "type": event_type,
            "data": data
        }
        await websocket.send_text(json.dumps(payload, default=str))


# Global singleton instance for single Uvicorn process
ws_manager = ConnectionManager()
