from abc import ABC, abstractmethod
from typing import Dict, Optional, List
import json
import os
from contextlib import contextmanager
import sqlite3
from dill import dump, load

class StorageBackend(ABC):
    """Abstract base class for workflow state storage backends."""
    
    @abstractmethod
    def save_state(self, workflow_id: str, run_id: str, save_data: dict) -> None:
        """Save the current workflow execution state."""
        pass
    
    @abstractmethod
    def load_state(self, workflow_id: str, run_id: str) -> Optional[Dict]:
        """Load a workflow execution state."""
        pass

    def list_runs(self, workflow_id: str) -> List[str]:
        """List all runs for a given workflow."""
        pass

    def list_workflows(self) -> List[str]:
        """List all workflows."""
        pass


class FileSystemStorage(StorageBackend):
    """File system implementation of storage backend."""
    
    def __init__(self, base_dir: str = "logs"):
        self.base_dir = base_dir
        
    def save_state(self, workflow_id: str, run_id: str, save_data: dict) -> None:
        log_dir = f"{self.base_dir}/{workflow_id}/{run_id}"
        os.makedirs(log_dir, exist_ok=True)
        dill_file = os.path.join(log_dir, "state.pkl")

        try:
            with open(dill_file, 'wb') as f:
                dump(save_data, f)
        except Exception as e:
            raise e
    
    def load_state(self, workflow_id: str, run_id: str) -> Optional[Dict]:
        dill_file = f"{self.base_dir}/{workflow_id}/{run_id}/state.pkl"
        if not os.path.exists(dill_file):
            return None
            
        with open(dill_file, 'rb') as f:
            return load(f)

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
    
    def save_state(self, workflow_id: str, run_id: str, save_data: dict) -> None:
        
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                '''
                INSERT OR REPLACE INTO workflow_states (workflow_id, run_id, state_json, updated_at)
                VALUES (?, ?, ?, CURRENT_TIMESTAMP)
                ''',
                (workflow_id, run_id, json.dumps(save_data))
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

def path_to_id(workflow_path):
    return os.path.splitext(os.path.normpath(workflow_path).replace('\\', '/'))[0].replace("/", ".")

def id_to_path(workflow_id, json=True):
    if json:
        return os.path.normpath(workflow_id.replace(".", "/") + ".json")
    else:
        return os.path.normpath(workflow_id.replace(".", "/") + ".py")
