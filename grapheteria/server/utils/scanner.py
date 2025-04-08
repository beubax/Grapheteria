from collections import defaultdict
import copy
import inspect
import os
import json
import importlib.util 
from grapheteria import Node, _NODE_REGISTRY
from grapheteria.utils import path_to_id
import sys
import time

temp = defaultdict(list)

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
                temp[cls.__module__].append([cls.__name__, code])
        
        # Replace the method globally
        Node.__init_subclass__ = classmethod(custom_init_subclass)

    @staticmethod
    def scan_nodes(manager):
        """Reload all Python modules to detect node classes""" 
        temp.clear()
        # Save original path
        original_path = sys.path.copy()
        
        try:
            # Add current directory to path if not already there
            cwd = os.getcwd()
            if cwd not in sys.path and '' not in sys.path:
                sys.path.insert(0, cwd)
            
            
            skip_dirs = {'venv', '__pycache__', 'grapheteria', 'logs', '.git', 'tests'}

            for root, dirs, files in os.walk('.'):
                # Remove directories to skip from dirs list to prevent recursion into them
                # This is done in-place and affects which directories os.walk visits
                if root == '.':
                    dirs[:] = [d for d in dirs if d not in skip_dirs]
                for file in files:
                    if file.endswith('.py'):
                        module_path = path_to_id(os.path.join(root, file))
                        SystemScanner._load_module(module_path, reload=False)

            manager.node_registry = copy.deepcopy(temp)
        finally:
            # Always restore original path
            sys.path = original_path

    @staticmethod
    async def scan_node_file(manager, file_path, deletion=False):
        temp.clear()
        # Skip processing if file is in a directory we want to ignore
        first_dir = file_path.split(os.sep)[1] if os.sep in file_path and file_path.startswith('./') else ''
        if first_dir in ('venv', '__pycache__', 'grapheteria', 'logs', '.git', 'tests'):
            return
        
        module_name = path_to_id(file_path)
        if deletion:
            del manager.node_registry[module_name]
        else:
            # Save original path
            original_path = sys.path.copy()
            
            try:
                # Add current directory to path if not already there
                cwd = os.getcwd()
                if cwd not in sys.path and '' not in sys.path:
                    sys.path.insert(0, cwd)
                SystemScanner._load_module(module_name)
                manager.node_registry[module_name] = temp.get(module_name, [])
            finally:
                # Restore original path
                sys.path = original_path
        
        await manager.broadcast_nodes()

    @staticmethod
    def scan_workflows(manager):
        """Scan directory for workflow JSON files"""
        found_workflows = {}
        
        skip_dirs = {'venv', '__pycache__', 'grapheteria', 'logs', '.git', 'tests'}
        
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
                if (workflow_id in manager.workflows) or (workflow_data and 'nodes' in workflow_data):
                    manager.workflows[workflow_id] = workflow_data
            await manager.broadcast_workflows()
        except Exception as e:
            print(f"In scanner class: Error loading workflow {file_path}: {e}")