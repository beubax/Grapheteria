import json
from fastapi import WebSocket
from typing import Set, Dict, Any, List


class OutboundHandler:
    @staticmethod
    async def send_to_websocket(websocket: WebSocket, message: Dict[str, Any]):
        """Send a message to a single WebSocket"""
        await websocket.send_text(json.dumps(message))

    @staticmethod
    async def send_to_all(clients: Set[WebSocket], message: Dict[str, Any]):
        """Send a message to all connected clients"""
        for client in clients:
            await OutboundHandler.send_to_websocket(client, message)

    @staticmethod
    async def send_initial_state(
        websocket: WebSocket, node_registry: Dict, workflows: Dict, tool_registry: Dict
    ):
        """Send initial application state to a new client"""
        await OutboundHandler.send_to_websocket(
            websocket,
            {
                "type": "init",
                "nodes": node_registry,
                "workflows": workflows,
                "tool_registry": {name: [url, registry.get_available_tools()] for name, [url, registry] in tool_registry.items()}
            },
        )

    @staticmethod
    async def broadcast_state(clients: Set[WebSocket], node_registry: Dict, workflows: Dict, tool_registry: Dict):
        """Broadcast node registry to all clients"""
        await OutboundHandler.send_to_all(
            clients,
            {
                "type": "updated_state", 
                "nodes": node_registry,
                "workflows": workflows,
                "tool_registry": {name: [url, registry.get_available_tools()] for name, [url, registry] in tool_registry.items()}
            },
        )
