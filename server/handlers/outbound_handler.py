import json
import asyncio
from machine import AsyncNode, SyncNode

class OutboundHandler:
    @staticmethod
    async def send_to_all(clients, message):
        if clients:
            await asyncio.gather(
                *[client.send(json.dumps(message)) for client in clients]
            )

    @staticmethod
    async def send_initial_state(websocket, node_registry, workflows):
        """Send complete initial state to new client"""
        await OutboundHandler._send_nodes(websocket, node_registry)
        await OutboundHandler._send_workflows(websocket, workflows)

    @staticmethod
    async def _send_nodes(websocket, node_registry):
        """Send registered node types to client"""
        node_list = [{
            "name": name,
            "type": "async" if issubclass(cls, AsyncNode) else "sync"
        } for name, cls in node_registry.items()]
        
        await websocket.send(json.dumps({
            "type": "available_nodes",
            "nodes": node_list
        }))

    @staticmethod
    async def _send_workflows(websocket, workflows):
        """Send all workflows to client"""
        await websocket.send(json.dumps({
            "type": "available_workflows",
            "workflows": list(workflows.values())
        }))

    @staticmethod
    async def broadcast_connection_status(clients, connected):
        """Notify all clients about connection status"""
        await OutboundHandler.send_to_all(clients, {
            "type": "connection_status", 
            "connected": connected
        })

    @staticmethod
    async def broadcast_nodes(clients, node_registry):
        """Notify all clients about updated node registry"""
        await OutboundHandler.send_to_all(clients, {
            "type": "available_nodes",
            "nodes": [{
                "name": name,
                "type": "async" if issubclass(cls, AsyncNode) else "sync"
            } for name, cls in node_registry.items()]
        })

    @staticmethod
    async def broadcast_workflows(clients, workflows):
        """Send all workflows to connected clients"""
        await OutboundHandler.send_to_all(clients, {
            "type": "available_workflows",
            "workflows": list(workflows.values())
        })