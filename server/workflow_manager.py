import json
import os
from fastapi import WebSocket
from server.handlers.inbound_handler import InboundHandler
from server.handlers.outbound_handler import OutboundHandler
from server.utils.scanner import SystemScanner

class WorkflowManager:
    def __init__(self):
        self.clients = set()
        self.node_registry = {}
        self.workflows = {}
        self.debug_sessions = {}  # Maps client -> {workflow_id, run_id}

    async def register(self, websocket: WebSocket):
        self.clients.add(websocket)
        await OutboundHandler.send_initial_state(websocket, self.node_registry, self.workflows)

    async def unregister(self, websocket: WebSocket):
        self.clients.remove(websocket)

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
        if workflow_id not in self.workflows:
            return

        workflow = self.workflows[workflow_id]
        file_path = f"{workflow_id}.json"
        
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

    async def handle_client_message(self, websocket, message):
        data = json.loads(message)
        await InboundHandler.handle_client_message(self, websocket, data)

    async def scan_workflow_file(self, file_path):
        """Scan a single workflow file that was modified"""
        try:
            with open(file_path, 'r') as f:
                workflow_data = json.load(f)
                workflow_id = os.path.splitext(os.path.basename(file_path))[0]
                self.workflows[workflow_id] = workflow_data
                await self.broadcast_workflows()
        except Exception as e:
            print(f"Error loading workflow {file_path}: {e}")