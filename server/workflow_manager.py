from machine.utils import id_to_path
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

    def scan_nodes(self):
        SystemScanner.scan_nodes(self)

    def scan_workflows(self):
        SystemScanner.scan_workflows(self)

    async def register(self, websocket: WebSocket):
        self.clients.add(websocket)
        await OutboundHandler.send_initial_state(websocket, self.node_registry, self.workflows)

    async def unregister(self, websocket: WebSocket):
        self.clients.remove(websocket)

    async def handle_client_message(self, websocket, message):
        data = json.loads(message)
        await InboundHandler.handle_client_message(self, websocket, data)

    async def broadcast_nodes(self):
        await OutboundHandler.broadcast_nodes(self.clients, self.node_registry)

    async def broadcast_workflows(self):
        await OutboundHandler.broadcast_workflows(self.clients, self.workflows)

    async def scan_node_file(self, file_path, deletion):
        await SystemScanner.scan_node_file(self, file_path, deletion)

    async def scan_workflow_file(self, file_path, deletion):
        await SystemScanner.scan_workflow_file(self, file_path, deletion)

    async def save_workflow(self, workflow_id):
        """Save workflow to original file"""
        if workflow_id not in self.workflows:
            return

        workflow = self.workflows[workflow_id]
        file_path = id_to_path(workflow_id)
        print(file_path)
        with open(file_path, 'w') as f:
            json.dump(workflow, f, indent=2)

    async def update_node_source(self, module: str, node_class_name: str, new_class_source: str) -> bool:
        """Update the source code for a node class without affecting other code in the file"""
        if module not in self.node_registry:
            return False
        
        source_file = id_to_path(module, json=False)
        try:
            import libcst as cst
            
            # Read the entire file
            with open(source_file, 'r') as f:
                file_content = f.read()
            
            # Parse the new class code to ensure it's valid Python
            try:
                cst.parse_module(new_class_source)
            except Exception as e:
                print(f"Invalid Python code provided: {e}")
                return False
            
            # Create a transformer to find and replace just this class
            class ClassReplacer(cst.CSTTransformer):
                def __init__(self, target_class_name, replacement_code):
                    self.target_class_name = target_class_name
                    self.replacement_code = replacement_code
                    self.replacement_tree = cst.parse_module(replacement_code)
                    self.found = False
                    
                def leave_ClassDef(self, original_node, updated_node):
                    if original_node.name.value == self.target_class_name:
                        # Extract just the class from the replacement code
                        for statement in self.replacement_tree.body:
                            if isinstance(statement, cst.ClassDef) and statement.name.value == self.target_class_name:
                                self.found = True
                                # Preserve the original leading whitespace
                                return statement.with_changes(
                                    leading_lines=original_node.leading_lines
                                )
                    return updated_node
                    
            # Apply the transformation
            module = cst.parse_module(file_content)
            transformer = ClassReplacer(node_class_name, new_class_source)
            modified_module = module.visit(transformer)
            
            if not transformer.found:
                print(f"Could not find class {node_class_name} in file")
                return False
            
            # Write the modified code back to the file
            with open(source_file, 'w') as f:
                f.write(modified_module.code)
            
            return True
        except Exception as e:
            print(f"Error updating source for {module}.{node_class_name}: {e}")
            return False

    

        