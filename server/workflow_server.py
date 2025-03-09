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
        self.debug_sessions = {}  # Maps client -> {workflow_id, run_id}

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

    async def process_log_update(self, workflow_id, run_id, log_file_path):
        """Process a log file update and notify only relevant clients in debug mode"""
        
        # Determine both possible file paths
        base_path = log_file_path[:-4] if log_file_path.endswith('.tmp') else log_file_path
        temp_path = f"{base_path}.tmp" if not log_file_path.endswith('.tmp') else log_file_path
        
        try:
            log_data = None
            # Try both paths
            for path in [base_path, temp_path]:
                try:
                    with open(path, 'r') as f:
                        log_data = json.load(f)
                    break  # Stop trying if we succeed
                except (FileNotFoundError, json.JSONDecodeError) as e:
                    continue  # Try the next path
                
            # Find clients that are debugging this specific run
            for client, session in self.debug_sessions.items():
                if session.get('run_id') == run_id and session.get('workflow_id') == workflow_id:
                    await OutboundHandler.send_execution_state(client, log_data)
            
        except Exception as e:
            print(f"Error processing log update for {log_file_path}: {e}")

    async def handle_client(self, websocket):
        await self.register(websocket)
        try:
            async for message in websocket:
                await self.handle_client_message(websocket, message)
        except websockets.exceptions.ConnectionClosed:
            pass
        finally:
            await self.unregister(websocket)
            # Clean up any debug session
            if websocket in self.debug_sessions:
                del self.debug_sessions[websocket]

    async def handle_client_message(self, websocket, message):
        data = json.loads(message)
        await InboundHandler.handle_client_message(self, websocket, data)

    async def scan_workflow_file(self, file_path):
        """Scan a single workflow file that was modified"""
        try:
            with open(file_path, 'r') as f:
                workflow_data = json.load(f)
                if workflow_id := workflow_data.get('workflow_id'):
                    self.workflows[workflow_id] = workflow_data
                    self.workflow_paths[workflow_id] = file_path
                    await self.broadcast_workflows()
        except Exception as e:
            print(f"Error loading workflow {file_path}: {e}")