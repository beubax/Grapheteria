import json
from fastapi import WebSocket
from typing import Set, Dict, Any

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
    async def send_initial_state(websocket: WebSocket, node_registry: Dict, workflows: Dict):
        """Send initial application state to a new client"""
        await OutboundHandler.send_to_websocket(websocket, {
            "type": "init",
            "nodes": [{
                "name": name,
                "type": "Node"
            } for name, cls in node_registry.items()],
            "workflows": workflows
        })
    
    @staticmethod
    async def broadcast_nodes(clients: Set[WebSocket], node_registry: Dict):
        """Broadcast node registry to all clients"""
        await OutboundHandler.send_to_all(clients, {
            "type": "available_nodes",
            "nodes": [{
                "name": name,
                "type": "Node"
            } for name, cls in node_registry.items()]
        })
    
    @staticmethod
    async def broadcast_workflows(clients: Set[WebSocket], workflows: Dict):
        """Broadcast workflows to all clients"""
        await OutboundHandler.send_to_all(clients, {
            "type": "available_workflows",
            "workflows": workflows
        })
    
    @staticmethod
    async def send_execution_state(client: WebSocket, log_data: Dict):
        """Send execution state update to a specific client"""
        await OutboundHandler.send_to_websocket(client, {
            "type": "execution_state",
            "log_data": log_data
        })


    @staticmethod
    async def send_workflow_runs(websocket, workflow_id, runs):
        """Send workflow runs to a client"""
        await websocket.send(json.dumps({
            "type": "workflow_runs_list",
            "workflow_id": workflow_id,
            "runs": runs
        }))
    
    @staticmethod
    async def send_run_states(websocket, workflow_id, run_id, states):
        """Send run states to a client"""
        await websocket.send(json.dumps({
            "type": "run_states_list",
            "workflow_id": workflow_id,
            "run_id": run_id,
            "states": states
        }))
    
    @staticmethod
    async def broadcast_workflow_runs(clients, workflow_id, runs):
        """Broadcast updated run list for a workflow"""
        await OutboundHandler.send_to_all(clients, {
            "type": "workflow_runs_update",
            "workflow_id": workflow_id,
            "runs": runs
        })