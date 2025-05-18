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
        websocket: WebSocket, node_registry: Dict, workflows: Dict, tools: List[Dict[str, str]], authenticated_tools: List[str]
    ):
        """Send initial application state to a new client"""
        await OutboundHandler.send_to_websocket(
            websocket,
            {
                "type": "init",
                "nodes": node_registry,
                "workflows": workflows,
                "tools": [tool for tool, auth in tools.items()],
                "authenticated_tools": list(set(authenticated_tools)),
            },
        )

    @staticmethod
    async def broadcast_state(clients: Set[WebSocket], node_registry: Dict, workflows: Dict):
        """Broadcast node registry to all clients"""
        await OutboundHandler.send_to_all(
            clients,
            {
                "type": "updated_state", 
                "nodes": node_registry,
                "workflows": workflows
            },
        )
