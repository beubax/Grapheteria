import os
import json
import importlib.util
from machine import BaseNode

class SystemScanner:
    @staticmethod
    def _load_module(root, file):
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

    @staticmethod
    async def scan_nodes(server):
        """Reload all Python modules to detect node classes"""
        server.node_registry.clear()
        BaseNode.clear_registry()
        
        for root, dirs, files in os.walk('.'):
            if any(skip in root for skip in ('venv', '__pycache__', 'ui')):
                continue
                
            for file in files:
                if file.endswith('.py'):
                    SystemScanner._load_module(root, file)

        server.node_registry.update(BaseNode.get_registry())
        await server.broadcast_nodes()

    @staticmethod
    async def scan_workflows(server):
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

        server.workflows = found_workflows
        server.workflow_paths = found_files
        await server.broadcast_workflows()