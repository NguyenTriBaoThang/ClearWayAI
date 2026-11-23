"""ClearWayAI Real-time WebSocket Stream & Pub/Sub Manager (`apps.api.src.websocket`).

Manages WebSocket client connections, subscription filtering, bidirectional commands,
and telemetry broadcast streaming per simulation episode and globally.
"""

from __future__ import annotations

import asyncio
import logging
import threading
import time
from typing import Any

from fastapi import WebSocket, WebSocketDisconnect

from apps.api.src.schemas import TelemetrySnapshotSchema

logger = logging.getLogger("clearway.websocket")


class WebSocketManager:
    """Thread-safe and async-safe WebSocket connection and pub/sub broadcaster."""

    def __init__(self) -> None:
        # channel_name -> set of active WebSockets (channels: "global", "telemetry", or "{simulation_id}")
        self._active_connections: dict[str, set[WebSocket]] = {}
        # websocket -> dictionary of subscription filter parameters
        self._client_filters: dict[WebSocket, dict[str, Any]] = {}
        self._lock = threading.Lock()

    @property
    def total_connections(self) -> int:
        """Return count of unique active WebSocket connections across all channels."""
        all_sockets: set[WebSocket] = set()
        for s_set in self._active_connections.values():
            all_sockets.update(s_set)
        return len(all_sockets)

    def get_channel_count(self, channel: str) -> int:
        """Return number of connections subscribed to a specific channel."""
        return len(self._active_connections.get(channel, set()))

    async def connect(self, websocket: WebSocket, channel: str = "global") -> None:
        """Accept a new WebSocket connection and register it to channel."""
        await websocket.accept()
        with self._lock:
            if channel not in self._active_connections:
                self._active_connections[channel] = set()
            self._active_connections[channel].add(websocket)
            self._client_filters[websocket] = {}
        logger.info(
            "WebSocket connected to channel '%s' (total: %d)", channel, self.total_connections
        )

    async def disconnect(self, websocket: WebSocket, channel: str = "global") -> None:
        """Unregister a WebSocket connection and clean up filters."""
        with self._lock:
            if channel in self._active_connections:
                self._active_connections[channel].discard(websocket)
                if not self._active_connections[channel]:
                    del self._active_connections[channel]
            self._client_filters.pop(websocket, None)
        logger.info(
            "WebSocket disconnected from channel '%s' (total: %d)", channel, self.total_connections
        )

    def set_filter(self, websocket: WebSocket, filter_options: dict[str, Any]) -> None:
        """Update subscription filtering parameters for a connected client."""
        self._client_filters[websocket] = filter_options

    def get_filter(self, websocket: WebSocket) -> dict[str, Any]:
        """Retrieve client subscription filters."""
        return self._client_filters.get(websocket, {})

    def _matches_filter(self, websocket: WebSocket, message: dict[str, Any]) -> bool:
        """Check if message matches client subscription filter criteria."""
        client_filter = self._client_filters.get(websocket, {})
        if not client_filter:
            return True

        # Filter by node_id if specified in filter
        target_node = client_filter.get("node_id")
        if target_node and "data" in message:
            data = message["data"]
            # Check intersection_id or approach
            if isinstance(data, dict):
                iid = data.get("intersection_id")
                if iid and iid != target_node:
                    return False

        # Filter by vehicle_id if specified in filter
        target_veh = client_filter.get("vehicle_id")
        if target_veh and "data" in message:
            data = message["data"]
            if isinstance(data, dict) and "vehicles" in data:
                veh_list = data["vehicles"]
                if isinstance(veh_list, list):
                    matching = any(
                        v.get("vehicle_id") == target_veh for v in veh_list if isinstance(v, dict)
                    )
                    if not matching:
                        return False

        return True

    async def broadcast_json(self, channel: str, message: dict[str, Any]) -> int:
        """Broadcast a JSON message to all subscribers of channel and global channels."""
        # Gather target channels: the specific channel, and if not already "global", also "global" and "telemetry"
        channels_to_notify = [channel]
        if channel not in ("global", "telemetry"):
            if "global" in self._active_connections:
                channels_to_notify.append("global")
            if "telemetry" in self._active_connections:
                channels_to_notify.append("telemetry")

        recipients: set[WebSocket] = set()
        for ch in channels_to_notify:
            recipients.update(self._active_connections.get(ch, set()))

        if not recipients:
            return 0

        dead_connections: list[tuple[WebSocket, str]] = []
        sent_count = 0

        for ws in recipients:
            if not self._matches_filter(ws, message):
                continue
            try:
                await ws.send_json(message)
                sent_count += 1
            except (WebSocketDisconnect, ConnectionResetError, RuntimeError):
                for ch in channels_to_notify:
                    if ch in self._active_connections and ws in self._active_connections[ch]:
                        dead_connections.append((ws, ch))

        # Cleanup disconnected sockets
        for ws, ch in dead_connections:
            await self.disconnect(ws, ch)

        return sent_count

    async def broadcast_snapshot(
        self,
        simulation_id: str,
        snapshot: TelemetrySnapshotSchema | dict[str, Any],
    ) -> int:
        """Broadcast a telemetry snapshot frame to simulation subscribers."""
        snapshot_dict = (
            snapshot.model_dump(mode="json")
            if isinstance(snapshot, TelemetrySnapshotSchema)
            else snapshot
        )

        message: dict[str, Any] = {
            "event": "snapshot",
            "simulation_id": simulation_id,
            "timestamp": time.time(),
            "data": snapshot_dict,
        }
        return await self.broadcast_json(simulation_id, message)

    async def broadcast_event(
        self,
        simulation_id: str,
        event_name: str,
        payload: dict[str, Any],
    ) -> int:
        """Broadcast an operational event (pre-clearance alert, safety intervention, etc.)."""
        message: dict[str, Any] = {
            "event": event_name,
            "simulation_id": simulation_id,
            "timestamp": time.time(),
            "data": payload,
        }
        return await self.broadcast_json(simulation_id, message)

    def broadcast_snapshot_sync(
        self,
        simulation_id: str,
        snapshot: TelemetrySnapshotSchema | dict[str, Any],
    ) -> None:
        """Async-safe synchronous trigger to broadcast snapshot if event loop is running."""
        try:
            loop = asyncio.get_running_loop()
            loop.create_task(self.broadcast_snapshot(simulation_id, snapshot))
        except RuntimeError:
            # Event loop not currently active in thread; non-blocking pass
            pass

    async def handle_client_message(
        self,
        websocket: WebSocket,
        channel: str,
        data: dict[str, Any],
    ) -> dict[str, Any]:
        """Dispatch incoming client command (ping, subscribe, control action)."""
        action = data.get("action", "")

        if action == "ping":
            return {
                "event": "pong",
                "simulation_id": channel,
                "timestamp": time.time(),
            }

        elif action == "subscribe":
            filter_opts = data.get("filter", {})
            self.set_filter(websocket, filter_opts)
            return {
                "event": "subscribed",
                "simulation_id": channel,
                "timestamp": time.time(),
                "filter": filter_opts,
            }

        elif action in ("pause", "resume", "play", "step", "seek", "speed"):
            # Acknowledge control command dispatched over WebSocket
            return {
                "event": f"command_ack_{action}",
                "simulation_id": channel,
                "timestamp": time.time(),
                "details": data,
            }

        else:
            return {
                "event": "error",
                "simulation_id": channel,
                "timestamp": time.time(),
                "message": f"Unsupported action '{action}'.",
            }


# Default global singleton WebSocket connection manager
ws_manager = WebSocketManager()
