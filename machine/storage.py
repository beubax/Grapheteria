from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List
import json
import os
from contextlib import contextmanager
import sqlite3

class StorageBackend(ABC):
    """Abstract base class for workflow state storage backends."""
    
    @abstractmethod
    def save_state(self, workflow_id: str, run_id: str, steps: List[dict]) -> None:
        """Save the current workflow execution state."""
        pass
    
    @abstractmethod
    def load_state(self, workflow_id: str, run_id: str) -> Optional[Dict]:
        """Load a workflow execution state."""
        pass

    @abstractmethod
    def list_runs(self, workflow_id: str) -> List[str]:
        """List all runs for a given workflow."""
        pass

    @abstractmethod
    def list_workflows(self) -> List[str]:
        """List all workflows."""
        pass


class FileSystemStorage(StorageBackend):
    """File system implementation of storage backend."""
    
    def __init__(self, base_dir: str = "logs"):
        self.base_dir = base_dir
        
    def save_state(self, workflow_id: str, run_id: str, steps: List[dict]) -> None:
        print(f"Saving state for workflow {workflow_id} with run_id {run_id}")
        log_dir = f"{self.base_dir}/{workflow_id}/{run_id}"
        os.makedirs(log_dir, exist_ok=True)
        state_file = os.path.join(log_dir, "state.json")
        
        data = {
            'workflow_id': workflow_id,
            'run_id': run_id,
            'steps': steps
        }
        
        # Efficient file writing with atomic operation
        temp_path = f"{state_file}.tmp"
        with open(temp_path, 'w') as f:
            json.dump(data, f)
        os.rename(temp_path, state_file)  # Atomic operation
    
    def load_state(self, workflow_id: str, run_id: str) -> Optional[Dict]:
        state_file = f"{self.base_dir}/{workflow_id}/{run_id}/state.json"
        if not os.path.exists(state_file):
            return None
            
        with open(state_file, 'r') as f:
            return json.load(f)

    def list_runs(self, workflow_id: str) -> List[str]:
        workflow_dir = f"{self.base_dir}/{workflow_id}"
        if not os.path.exists(workflow_dir):
            return []
            
        run_ids = [d for d in os.listdir(workflow_dir) 
                if os.path.isdir(os.path.join(workflow_dir, d))]
        run_ids.sort(reverse=True)
        return run_ids

    def list_workflows(self) -> List[str]:
        return [d for d in os.listdir(self.base_dir) 
                if os.path.isdir(os.path.join(self.base_dir, d))]


class SQLiteStorage(StorageBackend):
    """SQLite implementation of storage backend."""
    
    def __init__(self, db_path: str = "workflows.db"):
        self.db_path = db_path
        self._init_db()
        
    def _init_db(self):
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS workflow_states (
                workflow_id TEXT,
                run_id TEXT,
                state_json TEXT,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY (workflow_id, run_id)
            )
            ''')
            conn.commit()
    
    @contextmanager
    def _get_connection(self):
        conn = sqlite3.connect(self.db_path)
        try:
            yield conn
        finally:
            conn.close()
    
    def save_state(self, workflow_id: str, run_id: str, steps: List[dict]) -> None:
        data = {
            'workflow_id': workflow_id,
            'run_id': run_id,
            'steps': steps
        }
        
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                '''
                INSERT OR REPLACE INTO workflow_states (workflow_id, run_id, state_json, updated_at)
                VALUES (?, ?, ?, CURRENT_TIMESTAMP)
                ''',
                (workflow_id, run_id, json.dumps(data))
            )
            conn.commit()
    
    def load_state(self, workflow_id: str, run_id: str) -> Optional[Dict]:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT state_json FROM workflow_states WHERE workflow_id = ? AND run_id = ?",
                (workflow_id, run_id)
            )
            row = cursor.fetchone()
            
        if not row:
            return None
            
        return json.loads(row[0])
