import os
import json
import importlib.util
from machine import Node
from typing import List, Dict, Any, Optional
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
    async def scan_nodes(server):
        """Reload all Python modules to detect node classes"""
        server.node_registry.clear()
        Node.clear_registry()
        
        for root, dirs, files in os.walk('.'):
            if any(skip in root for skip in ('venv', '__pycache__', 'ui', 'server')):
                continue
                
            for file in files:
                if file.endswith('.py'):
                    SystemScanner._load_module(root, file)

        server.node_registry.update(Node.get_registry())
        await server.broadcast_nodes()

    @staticmethod
    async def scan_workflows(server):
        """Scan directory for workflow JSON files"""
        found_workflows = {}
        found_files = {}
        
        for root, dirs, files in os.walk('.'):
            if any(skip in root for skip in ('venv', '__pycache__', 'ui', 'server')):
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

    @staticmethod
    def get_state_files(run_dir: str) -> List[str]:
        """Get all state files for a run, sorted by timestamp"""
        if not os.path.exists(run_dir):
            return []
            
        state_files = glob.glob(f"{run_dir}/state_*.json")
        return sorted(state_files, key=os.path.getmtime)
    
    @staticmethod
    async def get_workflow_runs(workflow_id: str) -> List[Dict[str, Any]]:
        """Get all runs for a specific workflow"""
        workflow_log_dir = f"logs/{workflow_id}"
        if not os.path.exists(workflow_log_dir):
            return []
            
        # Get all run folders
        run_dirs = [d for d in os.listdir(workflow_log_dir) 
                   if os.path.isdir(os.path.join(workflow_log_dir, d))]
        
        runs = []
        for run_id in run_dirs:
            run_dir = os.path.join(workflow_log_dir, run_id)
            state_files = SystemScanner.get_state_files(run_dir)
            
            if state_files:
                # Get times from first and last state file
                with open(state_files[0], 'r') as f:
                    first_state = json.load(f)
                with open(state_files[-1], 'r') as f:
                    last_state = json.load(f)
                    
                runs.append({
                    "run_id": run_id,
                    "start_time": first_state.get('metadata', {}).get('save_time'),
                    "end_time": last_state.get('metadata', {}).get('save_time'),
                    "status": last_state.get('workflow_status', "UNKNOWN"),
                    "state_count": len(state_files)
                })
                
        return sorted(runs, key=lambda x: x.get("start_time", ""), reverse=True)
    
    @staticmethod
    async def get_run_states(workflow_id: str, run_id: str) -> List[Dict[str, Any]]:
        """Get all states for a specific run"""
        run_dir = f"logs/{workflow_id}/{run_id}"
        state_files = SystemScanner.get_state_files(run_dir)
        
        states = []
        for state_file in state_files:
            with open(state_file, 'r') as f:
                state_data = json.load(f)
                states.append(state_data)
                
        return states
    
    @staticmethod
    def parse_log_path(log_file_path: str) -> Optional[tuple]:
        """Extract workflow name and run ID from log file path"""
        path_parts = log_file_path.split(os.path.sep)
        if len(path_parts) >= 4 and path_parts[-4] == "logs":
            workflow_id = path_parts[-3]
            run_id = path_parts[-2]
            return (workflow_id, run_id)
        return None