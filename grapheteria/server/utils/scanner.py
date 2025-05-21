from collections import defaultdict
import copy
import inspect
import os
import json
import importlib.util
from grapheteria import Node, _NODE_REGISTRY
from toolregistry import ToolRegistry
from grapheteria.utils import path_to_id
import sys

temp = defaultdict(dict)

class SystemScanner:
    @staticmethod
    def _load_module(module_path, reload=True):
        """Load/reload a Python module from file system"""
        try:
            module = importlib.import_module(module_path)
            if reload:
                importlib.reload(module)
        except ImportError:
            print(f"Could not load module from {module_path}")

    @staticmethod
    def setup_node_registry():
        """Setup the Node.__init_subclass__ method to properly register nodes"""

        def custom_init_subclass(cls, **kwargs):
            """Modified auto-register that properly captures nodes based on module"""
            super(Node, cls).__init_subclass__(**kwargs)
            if not inspect.isabstract(cls):
                _NODE_REGISTRY[cls.__name__] = cls
                code = inspect.getsource(cls)
                module_parts = cls.__module__.split('.')
                if len(module_parts) > 1:
                    folder_name = module_parts[0]
                    temp[folder_name][cls.__name__] = [code, cls.__module__]

        # Replace the method globally
        Node.__init_subclass__ = classmethod(custom_init_subclass)

    @staticmethod
    async def scan_system(manager):
        """Scan directory for both Python node files and workflow JSON files in a single pass"""
        # Clear existing temporary data
        temp.clear()
        found_workflows = {}

        # List of directories to skip
        skip_dirs = {
            "venv",
            "__pycache__",
            "grapheteria",
            "logs",
            ".github",
            "tests",
            "examples",
            "backups",
        }

        # Save original path
        original_path = sys.path.copy()

        try:
            # Add current directory to path if not already there
            cwd = os.getcwd()
            if cwd not in sys.path and "" not in sys.path:
                sys.path.insert(0, cwd)

            mcp_mappings = {}
            if os.path.exists("mcp.json"):
                with open("mcp.json", "r") as f:
                    mcp_mappings = json.load(f)
            
            for mcp_name, mcp_url in mcp_mappings.items():
                registry = ToolRegistry()
                try:
                    await registry.register_from_mcp_async(mcp_url)
                except Exception as e:
                    print(f"Error loading tool registry {mcp_name}: {e}")
                manager.tool_registry[mcp_name] = [mcp_url, registry]

            for root, dirs, files in os.walk("."):
                # Remove directories to skip from dirs list to prevent recursion into them
                dirs[:] = [d for d in dirs if d not in skip_dirs]

                # Skip processing files in the root directory
                if root == "." or root == "./":
                    continue

                # Extract the top directory name (not root) to use as key
                path_parts = root.split(os.sep)
                top_dir = path_parts[1] if len(path_parts) > 1 and path_parts[1] not in ["", "."] else None
                
                # Skip if we couldn't determine a valid top directory
                if not top_dir:
                    continue

                for file in files:
                    file_path = os.path.join(root, file)
                    
                    # Process Python files
                    if file.endswith(".py"):
                        module_path = path_to_id(file_path)
                        SystemScanner._load_module(module_path, reload=False)
                    
                    # Process schema.json files
                    elif file == "schema.json":
                        try:
                            with open(file_path, "r") as f:
                                workflow_data = json.load(f)
                            if workflow_data and "nodes" in workflow_data:
                                # Use top directory name as key
                                found_workflows[top_dir] = workflow_data
                        except Exception as e:
                            print(f"Error loading workflow {file_path}: {e}")

            # Update manager with found nodes and workflows
            manager.node_registry = copy.deepcopy(temp)
            manager.workflows = copy.deepcopy(found_workflows)
        finally:
            # Always restore original path
            sys.path = original_path

    @staticmethod
    async def scan_workflow(manager, file_path):
        """
        Unified function to scan a directory for both Python node files and workflow JSON files.
        This will update the manager's node registry and workflows data.
        """
        if file_path == "./mcp.json":
            mcp_mappings = {}
            if os.path.exists("mcp.json"):
                with open("mcp.json", "r") as f:
                    mcp_mappings = json.load(f)
            
            for mcp_name, mcp_url in mcp_mappings.items():
                if mcp_name in manager.tool_registry and mcp_url == manager.tool_registry[mcp_name][0]:
                    continue
                registry = ToolRegistry()
                try:
                    await registry.register_from_mcp_async(mcp_url)
                except Exception as e:
                    print(f"Error loading tool registry {mcp_name}: {e}")
                manager.tool_registry[mcp_name] = [mcp_url, registry]
            
            await manager.broadcast_state()
            return

        directory_path = os.path.dirname(file_path)
        # Skip if directory is the root directory
        if directory_path == "" or directory_path == "." or directory_path == "./":
            return
        
        # List of directories to skip
        skip_dirs = {
            "venv",
            "__pycache__",
            "grapheteria",
            "logs",
            ".github",
            "tests",
            "examples",
            "backups",
        }

        # Extract the top directory name to use as key
        path_parts = directory_path.split(os.sep)
        top_dir = path_parts[1] if len(path_parts) > 1 and path_parts[1] not in ["", "."] else None
        # Skip if we couldn't determine a valid top directory
        if not top_dir:
            return
            
        # Check if the directory is a forbidden directory
        if top_dir in skip_dirs:
            return
        
        # Check if directory exists
        if not os.path.exists(directory_path):
            # Remove from node registry if exists
            if top_dir in manager.node_registry:
                del manager.node_registry[top_dir]
            
            # Remove from workflows if exists
            if top_dir in manager.workflows:
                del manager.workflows[top_dir]
                
            # Broadcast updates
            await manager.broadcast_state()
            
            return

        # Save original path
        original_path = sys.path.copy()
        temp.clear()
        workflow_data = None

        try:
            # Add current directory to path if not already there
            cwd = os.getcwd()
            if cwd not in sys.path and "" not in sys.path:
                sys.path.insert(0, cwd)
                
            # Walk through all files in the directory
            for root, dirs, files in os.walk(top_dir):
                # Skip forbidden directories
                dirs[:] = [d for d in dirs if d not in skip_dirs]
                
                for file in files:
                    file_path = os.path.join(root, file)
                    
                    # Process Python files
                    if file.endswith(".py"):
                        module_path = path_to_id(file_path)
                        SystemScanner._load_module(module_path)
                    # Process schema.json files
                    elif file == "schema.json":
                        try:
                            with open(file_path, "r") as f:
                                workflow_data = json.load(f)
                        except Exception as e:
                            print(f"Error loading workflow {file_path}: {e}")
            
            # Update the manager's node registry with the new nodes from this directory
            if top_dir in temp:
                manager.node_registry[top_dir] = temp[top_dir]
            elif top_dir in manager.node_registry:
                # No nodes found but directory exists, clear previous nodes
                del manager.node_registry[top_dir]

            # Update workflow data if found
            if workflow_data and "nodes" in workflow_data:
                manager.workflows[top_dir] = workflow_data
            elif top_dir in manager.workflows:
                # No workflow found but directory exists, remove previous workflow
                del manager.workflows[top_dir]
            # Broadcast updates
            await manager.broadcast_state()
        finally:
            # Restore original path
            sys.path = original_path