from grapheteria.utils import id_to_path
import json
import os
from fastapi import WebSocket
from grapheteria.server.handlers.inbound_handler import InboundHandler
from grapheteria.server.handlers.outbound_handler import OutboundHandler
from grapheteria.server.utils.scanner import SystemScanner


class WorkflowManager:
    def __init__(self):
        self.clients = set()
        self.node_registry = {}
        self.workflows = {}

    def setup_node_registry(self):
        SystemScanner.setup_node_registry()

    def scan_nodes(self):
        SystemScanner.scan_nodes(self)

    def scan_workflows(self):
        SystemScanner.scan_workflows(self)

    async def register(self, websocket: WebSocket):
        self.clients.add(websocket)
        await OutboundHandler.send_initial_state(
            websocket, self.node_registry, self.workflows
        )

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
        with open(file_path, "w") as f:
            json.dump(workflow, f, indent=2)

    async def create_workflow(self, workflow_id: str):
        if workflow_id in self.workflows:
            return

        workflow = {
            "nodes": [],
        }
        file_path = id_to_path(workflow_id)
        with open(file_path, "w") as f:
            json.dump(workflow, f, indent=2)

    async def update_node_source(
        self, module: str, node_class_name: str, new_class_source: str
    ) -> bool:
        """Update the source code for a node class without affecting other code in the file"""
        if module not in self.node_registry:
            return False

        source_file = id_to_path(module, json=False)
        try:
            import libcst as cst

            # Read the entire file
            with open(source_file, "r") as f:
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
                            if (
                                isinstance(statement, cst.ClassDef)
                                and statement.name.value == self.target_class_name
                            ):
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
            with open(source_file, "w") as f:
                f.write(modified_module.code)

            return True
        except Exception as e:
            print(f"Error updating source for {module}.{node_class_name}: {e}")
            return False

    async def save_node_source(
        self, module: str, node_class_name: str, new_class_source: str
    ) -> bool:
        """Add a new node class to a module. If the module doesn't exist, it will be created."""
        source_file = id_to_path(module, json=False)

        try:
            import libcst as cst

            # Parse the new class code to ensure it's valid Python
            try:
                cst.parse_module(new_class_source)
            except Exception as e:
                print(f"Invalid Python code provided: {e}")
                return False

            # Create module directory if it doesn't exist
            os.makedirs(os.path.dirname(source_file), exist_ok=True)

            # If the file doesn't exist, create it with the new class
            if not os.path.exists(source_file):
                # Add import statement before the class source
                file_content = "from grapheteria import Node\n\n" + new_class_source
                with open(source_file, "w") as f:
                    f.write(file_content)

                return True

            # If file exists, read it and append the new class
            with open(source_file, "r") as f:
                file_content = f.read()

            # Check if the class already exists in the file
            module_tree = cst.parse_module(file_content)

            class ClassFinder(cst.CSTVisitor):
                def __init__(self, target_class_name):
                    self.target_class_name = target_class_name
                    self.found = False

                def visit_ClassDef(self, node):
                    if node.name.value == self.target_class_name:
                        self.found = True

            # Check if class already exists
            finder = ClassFinder(node_class_name)
            module_tree.visit(finder)

            if finder.found:
                print(f"Class {node_class_name} already exists in {module}")
                return False

            # Extract the class from the new_class_source
            new_class_module = cst.parse_module(new_class_source)
            new_class = None

            for statement in new_class_module.body:
                if (
                    isinstance(statement, cst.ClassDef)
                    and statement.name.value == node_class_name
                ):
                    new_class = statement
                    break

            if not new_class:
                print(f"Could not find class {node_class_name} in the provided source")
                return False

            # Add the class to the end of the file
            modified_module = module_tree.with_changes(
                body=module_tree.body
                + tuple(
                    [cst.EmptyLine(indent=True), cst.EmptyLine(indent=True), new_class]
                )
            )

            # Write the modified code back to the file
            with open(source_file, "w") as f:
                f.write(modified_module.code)
            return True
        except Exception as e:
            print(f"Error adding source for {module}.{node_class_name}: {e}")
            return False
