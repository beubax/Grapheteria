import json
import websockets
from server.handlers.inbound_handler import InboundHandler
from server.handlers.outbound_handler import OutboundHandler
from server.utils.scanner import SystemScanner

class WorkflowServer:
    def __init__(self):
        self.clients = set()
        self.node_registry = {}
        self.workflows = {}
        self.workflow_paths = {}

    async def register(self, websocket):
        self.clients.add(websocket)
        await OutboundHandler.send_initial_state(websocket, self.node_registry, self.workflows)
        await OutboundHandler.broadcast_connection_status(self.clients, True)

    async def unregister(self, websocket):
        self.clients.remove(websocket)
        await OutboundHandler.broadcast_connection_status(self.clients, False)

    async def send_to_all(self, message):
        await OutboundHandler.send_to_all(self.clients, message)

    async def broadcast_nodes(self):
        await OutboundHandler.broadcast_nodes(self.clients, self.node_registry)

    async def broadcast_workflows(self):
        await OutboundHandler.broadcast_workflows(self.clients, self.workflows)

    async def scan_nodes(self):
        await SystemScanner.scan_nodes(self)

    async def scan_workflows(self):
        await SystemScanner.scan_workflows(self)

    async def save_workflow(self, workflow_id):
        """Save workflow to original file"""
        if workflow_id not in self.workflows or workflow_id not in self.workflow_paths:
            return

        workflow = self.workflows[workflow_id]
        file_path = self.workflow_paths[workflow_id]
        
        with open(file_path, 'w') as f:
            json.dump(workflow, f, indent=2)

    async def handle_client(self, websocket):
        await self.register(websocket)
        try:
            async for message in websocket:
                await self.handle_client_message(websocket, message)
        except websockets.exceptions.ConnectionClosed:
            pass
        finally:
            await self.unregister(websocket)

    async def handle_client_message(self, websocket, message):
        data = json.loads(message)
        await InboundHandler.handle_client_message(self, websocket, data)