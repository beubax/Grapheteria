from collections import defaultdict
import inspect
import os
import json
import importlib.util
from machine import Node   
from machine.utils import path_to_id

class SystemScanner:
    @staticmethod
    def _load_module(module_path):
        """Load/reload a Python module from file system"""
        try:
            module = importlib.import_module(module_path)
            importlib.reload(module)
        except ImportError:
                print(f"Could not load module from {module_path}")

    @staticmethod
    def populate_node_registry(manager, node_registry):
        temp = defaultdict(list)
        for name, cls in node_registry.items():
            code = inspect.getsource(cls)
            temp[cls.__module__].append([name, code])

        manager.node_registry.update(temp)
        return

    @staticmethod
    def scan_nodes(manager):
        """Reload all Python modules to detect node classes"""
        
        skip_dirs = {'venv', '__pycache__', 'ui', 'server', 'logs', 'machine', '.git'}
        
        for root, dirs, files in os.walk('.'):
            # Remove directories to skip from dirs list to prevent recursion into them
            # This is done in-place and affects which directories os.walk visits
            if root == '.':
                dirs[:] = [d for d in dirs if d not in skip_dirs]
                
            for file in files:
                if file.endswith('.py'):
                    module_path = path_to_id(os.path.join(root, file))
                    SystemScanner._load_module(module_path)

        SystemScanner.populate_node_registry(manager, Node.get_registry())

    @staticmethod
    async def scan_node_file(manager, file_path, deletion=False):
        Node.clear_registry()
        # Skip processing if file is in a directory we want to ignore
        first_dir = file_path.split(os.sep)[1] if os.sep in file_path and file_path.startswith('./') else ''
        if first_dir in ('venv', '__pycache__', 'ui', 'server', 'logs', 'machine'):
            return
        
        module_name = path_to_id(file_path)
        if deletion:
            del manager.node_registry[module_name]
        else:
            SystemScanner._load_module(module_name)
            SystemScanner.populate_node_registry(manager, Node.get_registry())

        await manager.broadcast_nodes()

    @staticmethod
    def scan_workflows(manager):
        """Scan directory for workflow JSON files"""
        found_workflows = {}
        
        skip_dirs = {'venv', '__pycache__', 'ui', 'server', 'logs', 'machine', '.git'}
        
        for root, dirs, files in os.walk('.'):
            # Remove directories to skip from dirs list to prevent recursion into them
            if root == '.':
                dirs[:] = [d for d in dirs if d not in skip_dirs]
                
            for file in files:
                if file.endswith('.json'):
                    file_path = os.path.join(root, file)
                    try:
                        with open(file_path, 'r') as f:
                            workflow_data = json.load(f)
                        if workflow_data and 'nodes' in workflow_data:
                            workflow_id = path_to_id(file_path)
                            found_workflows[workflow_id] = workflow_data
                    except Exception as e:
                        print(f"Error loading workflow {file_path}: {e}")

        manager.workflows = found_workflows

    @staticmethod
    async def scan_workflow_file(manager, file_path, deletion=False):
        """Scan a single workflow file that was modified"""
        try:
            workflow_id = path_to_id(file_path)
            if deletion:
                del manager.workflows[workflow_id]
            else:
                with open(file_path, 'r') as f:
                    workflow_data = json.load(f)
                if workflow_data and 'nodes' in workflow_data:
                    manager.workflows[workflow_id] = workflow_data
            await manager.broadcast_workflows()
        except Exception as e:
            print(f"In scanner class: Error loading workflow {file_path}: {e}")