import asyncio
import websockets
import json
import os
import importlib.util
import inspect
import webbrowser
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from machine import AsyncNode, SyncNode, BaseNode
import time

class FileChangeHandler(FileSystemEventHandler):
    """Base class for handling file system changes with debouncing"""
    def __init__(self, server, extension):
        self.server = server
        self.last_scan = 0
        self.loop = asyncio.get_event_loop()
        self.extension = extension

    def on_modified(self, event):
        """Handle file modification events with 1-second debounce"""
        if event.src_path.endswith(self.extension):
            current_time = time.time()
            if current_time - self.last_scan > 1.0:  # 1-second debounce
                self.last_scan = current_time
                self.trigger_scan()

class NodeChangeHandler(FileChangeHandler):
    """Handles Python file changes for node definitions"""
    def __init__(self, server):
        super().__init__(server, '.py')

    def trigger_scan(self):
        """Trigger node scanning in the server's event loop"""
        asyncio.run_coroutine_threadsafe(
            self.server.scan_nodes(), 
            self.loop
        )

class WorkflowChangeHandler(FileChangeHandler):
    """Handles JSON file changes for workflow definitions"""
    def __init__(self, server):
        super().__init__(server, '.json')

    def trigger_scan(self):
        """Trigger workflow scanning in the server's event loop"""
        asyncio.run_coroutine_threadsafe(
            self.server.scan_workflows(),
            self.loop
        )

class WorkflowServer:
    """Main server handling WebSocket connections and file management"""
    def __init__(self):
        self.clients = set()
        self.node_registry = {}  # {node_name: node_class}
        self.workflows = {}      # {workflow_id: workflow_data}
        self.workflow_paths = {}# {workflow_id: file_path}

    async def register(self, websocket):
        self.clients.add(websocket)
        # Send initial data to new client
        await self.send_initial_state(websocket)
        # Notify all clients about connection status
        await self.send_to_all({"type": "connection_status", "connected": True})

    async def unregister(self, websocket):
        self.clients.remove(websocket)
        # Notify remaining clients about connection status
        await self.send_to_all({"type": "connection_status", "connected": False})

    async def send_to_all(self, message):
        if self.clients:
            await asyncio.gather(
                *[client.send(json.dumps(message)) for client in self.clients]
            )

    async def send_initial_state(self, websocket):
        """Send complete initial state to new client"""
        await self._send_nodes(websocket)
        await self._send_workflows(websocket)

    async def _send_nodes(self, websocket):
        """Send registered node types to client"""
        node_list = [{
            "name": name,
            "type": "async" if issubclass(cls, AsyncNode) else "sync"
        } for name, cls in self.node_registry.items()]
        
        await websocket.send(json.dumps({
            "type": "available_nodes",
            "nodes": node_list
        }))

    async def _send_workflows(self, websocket):
        """Send all workflows to client"""
        await websocket.send(json.dumps({
            "type": "available_workflows",
            "workflows": list(self.workflows.values())
        }))

    async def scan_nodes(self):
        """Reload all Python modules to detect node classes"""
        self.node_registry.clear()
        BaseNode.clear_registry()
        
        for root, dirs, files in os.walk('.'):
            if any(skip in root for skip in ('venv', '__pycache__', 'ui')):
                continue
                
            for file in files:
                if file.endswith('.py'):
                    self._load_module(root, file)

        self.node_registry.update(BaseNode.get_registry())
        await self._broadcast_nodes()

    def _load_module(self, root, file):
        """Load/reload a Python module from file system"""
        file_path = os.path.join(root, file)
        module_name = file[:-3]
        try:
            module = importlib.import_module(module_name)
            importlib.reload(module)
        except ImportError:
            spec = importlib.util.spec_from_file_location(module_name, file_path)
            if spec and spec.loader:
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)

    async def _broadcast_nodes(self):
        """Notify all clients about updated node registry"""
        await self.send_to_all({
            "type": "available_nodes",
            "nodes": [{
                "name": name,
                "type": "async" if issubclass(cls, AsyncNode) else "sync"
            } for name, cls in self.node_registry.items()]
        })

    async def scan_workflows(self):
        """Scan directory for workflow JSON files"""
        found_workflows = {}
        found_files = {}
        
        for root, _, files in os.walk('.'):
            if 'venv' in root or 'ui' in root:
                continue
                
            for file in files:
                if file.endswith('.json'):
                    file_path = os.path.join(root, file)
                    try:
                        with open(file_path, 'r') as f:
                            workflow_data = json.load(f)
                            if workflow_id := workflow_data.get('workflow_id'):
                                found_workflows[workflow_id] = workflow_data
                                found_files[workflow_id] = file_path
                    except Exception as e:
                        print(f"Error loading workflow {file_path}: {e}")

        self.workflows = found_workflows
        self.workflow_paths = found_files
        await self.broadcast_workflows()

    async def broadcast_workflows(self):
        """Send all workflows to connected clients"""
        await self.send_to_all({
            "type": "available_workflows",
            "workflows": list(self.workflows.values())
        })

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
        print("I am in handle client message")
        print(data)
        workflow_id = data.get('workflow_id')
        
        if not workflow_id or workflow_id not in self.workflows:
            return
            
        workflow = self.workflows[workflow_id]
        print(workflow)
        match data['type']:
            case 'node_created':
                # Prevent duplicate node IDs
                if any(n['id'] == data['nodeId'] for n in workflow['nodes']):
                    return
                    
                workflow['nodes'].append({
                    'id': data['nodeId'],
                    'class': data['nodeType'],
                    'config': {}
                })
                await self.save_workflow(workflow_id)
                
            case 'node_deleted':
                node_id = data['nodeId']
                # Remove node and ALL its edges
                workflow['nodes'] = [n for n in workflow['nodes'] if n['id'] != node_id]
                workflow['edges'] = [e for e in workflow['edges'] 
                                    if e['from'] != node_id and e['to'] != node_id]
                await self.save_workflow(workflow_id)
                
            case 'edge_created':
                # Check for existing edge and valid nodes
                from_node = data['from']
                to_node = data['to']
                existing = any(e['from'] == from_node and e['to'] == to_node 
                              for e in workflow['edges'])
                nodes_exist = (any(n['id'] == from_node for n in workflow['nodes']) and
                              any(n['id'] == to_node for n in workflow['nodes']))
                
                if not existing and nodes_exist:
                    workflow['edges'].append({
                        'from': from_node,
                        'to': to_node,
                        'condition': 'True'
                    })
                    await self.save_workflow(workflow_id)
                    
            case 'edge_deleted':
                # Exact match removal
                workflow['edges'] = [
                    e for e in workflow['edges']
                    if not (e['from'] == data['from'] and e['to'] == data['to'])
                ]
                await self.save_workflow(workflow_id)

    async def save_workflow(self, workflow_id):
        """Save workflow to original file and broadcast update"""
        if workflow_id not in self.workflows or workflow_id not in self.workflow_paths:
            return

        workflow = self.workflows[workflow_id]
        file_path = self.workflow_paths[workflow_id]
        
        # Save to original file
        with open(file_path, 'w') as f:
            json.dump(workflow, f, indent=2)

async def main():
    """Main server entry point"""
    server = WorkflowServer()
    
    # Configure file system watchers
    observer = Observer()
    observer.schedule(NodeChangeHandler(server), path='.', recursive=True)
    observer.schedule(WorkflowChangeHandler(server), path='.', recursive=True)
    observer.start()

    # Initial system scan
    await server.scan_nodes()
    await server.scan_workflows()
    
    # Launch client interface
    webbrowser.open('file://' + os.path.abspath('index.html'))
    
    # Start WebSocket server
    async with websockets.serve(
        server.handle_client,
        "localhost",
        8765,
        ping_interval=None
    ):
        print("WebSocket server started at ws://localhost:8765")
        await asyncio.Future()  # Run indefinitely

if __name__ == "__main__":
    asyncio.run(main())
