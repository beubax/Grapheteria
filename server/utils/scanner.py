import os
import json
import importlib.util
from typing import List, Dict, Any, Optional
from core.machine import Node
import glob

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
    async def scan_nodes(manager):
        """Reload all Python modules to detect node classes"""
        manager.node_registry.clear()
        Node.clear_registry()
        
        for root, dirs, files in os.walk('.'):
            if any(skip in root for skip in ('venv', '__pycache__', 'ui', 'server', 'logs', 'core')):
                continue
                
            for file in files:
                if file.endswith('.py') and file != 'machine.py':
                    SystemScanner._load_module(root, file)

        manager.node_registry.update(Node.get_registry())
        await manager.broadcast_nodes()

    @staticmethod
    async def scan_workflows(manager):
        """Scan directory for workflow JSON files"""
        found_workflows = {}
        
        for root, dirs, files in os.walk('.'):
            if any(skip in root for skip in ('venv', '__pycache__', 'ui', 'server', 'logs', 'core')):
                continue
                
            for file in files:
                if file.endswith('.json'):
                    file_path = os.path.join(root, file)
                    try:
                        with open(file_path, 'r') as f:
                            workflow_data = json.load(f)
                            workflow_id = os.path.splitext(os.path.basename(file_path))[0]
                            found_workflows[workflow_id] = workflow_data
                    except Exception as e:
                        print(f"Error loading workflow {file_path}: {e}")

        manager.workflows = found_workflows
        await manager.broadcast_workflows()