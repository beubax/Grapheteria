import pytest
import os
import json
import shutil
import tempfile
import sqlite3
from contextlib import contextmanager
from typing import Dict, List, Optional

from grapheteria.utils import StorageBackend, FileSystemStorage, SQLiteStorage

# Test fixtures
@pytest.fixture
def temp_dir():
    """Create a temporary directory for filesystem storage tests."""
    temp_dir = tempfile.mkdtemp()
    yield temp_dir
    # Cleanup after tests
    shutil.rmtree(temp_dir)

@pytest.fixture
def temp_db_path():
    """Create a temporary SQLite database path."""
    _, db_path = tempfile.mkstemp(suffix='.db')
    yield db_path
    # Cleanup after tests
    os.unlink(db_path)

@pytest.fixture
def fs_storage(temp_dir):
    """Return a FileSystemStorage instance using a temporary directory."""
    return FileSystemStorage(base_dir=temp_dir)

@pytest.fixture
def sqlite_storage(temp_db_path):
    """Return a SQLiteStorage instance using a temporary database."""
    return SQLiteStorage(db_path=temp_db_path)

@pytest.fixture
def sample_state():
    """Return a sample workflow state for testing."""
    return {
        "workflow_id": "test.workflow",
        "run_id": "20230101_120000_123",
        "steps": [
            {
                "shared": {"key": "value"},
                "next_node_id": "node1",
                "workflow_status": "HEALTHY",
                "node_statuses": {"start": "completed"},
                "awaiting_input": None,
                "previous_node_id": "start",
                "metadata": {"step": 1}
            }
        ]
    }


# FileSystemStorage Tests
class TestFileSystemStorage:
    def test_save_and_load_state(self, fs_storage, sample_state):
        """Test basic save and load functionality."""
        workflow_id = "test.workflow"
        run_id = "test_run_1"
        
        # Save state
        fs_storage.save_state(workflow_id, run_id, sample_state)
        
        # Load state
        loaded_state = fs_storage.load_state(workflow_id, run_id)
        
        # Verify state was properly saved and loaded
        assert loaded_state == sample_state
    
    def test_list_runs(self, fs_storage, sample_state):
        """Test listing runs for a workflow."""
        workflow_id = "test.workflow"
        run_ids = ["run_1", "run_2", "run_3"]
        
        # Create multiple runs
        for run_id in run_ids:
            fs_storage.save_state(workflow_id, run_id, sample_state)
        
        # List runs
        listed_runs = fs_storage.list_runs(workflow_id)
        
        # Verify all runs are listed
        assert set(listed_runs) == set(run_ids)
        
    def test_list_workflows(self, fs_storage, sample_state):
        """Test listing all workflows."""
        workflow_ids = ["test.workflow1", "test.workflow2", "test.workflow3"]
        run_id = "run_1"
        
        # Create multiple workflows
        for workflow_id in workflow_ids:
            fs_storage.save_state(workflow_id, run_id, sample_state)
        
        # List workflows
        listed_workflows = fs_storage.list_workflows()
        
        # Verify all workflows are listed
        assert set(listed_workflows) == set(workflow_ids)
    
    def test_load_nonexistent_state(self, fs_storage):
        """Test loading a non-existent workflow state."""
        loaded_state = fs_storage.load_state("nonexistent", "nonexistent")
        assert loaded_state is None
    
    def test_list_runs_nonexistent_workflow(self, fs_storage):
        """Test listing runs for a non-existent workflow."""
        runs = fs_storage.list_runs("nonexistent")
        assert runs == []
    
    def test_state_update(self, fs_storage, sample_state):
        """Test updating an existing state."""
        workflow_id = "test.workflow"
        run_id = "test_run"
        
        # Save initial state
        fs_storage.save_state(workflow_id, run_id, sample_state)
        
        # Update state
        updated_state = sample_state.copy()
        updated_state["steps"].append({
            "shared": {"key": "updated"},
            "next_node_id": "node2",
            "workflow_status": "RUNNING",
            "node_statuses": {"node1": "completed"},
            "awaiting_input": None,
            "previous_node_id": "node1",
            "metadata": {"step": 2}
        })
        
        # Save updated state
        fs_storage.save_state(workflow_id, run_id, updated_state)
        
        # Load state
        loaded_state = fs_storage.load_state(workflow_id, run_id)
        
        # Verify state was updated
        assert loaded_state == updated_state
        assert len(loaded_state["steps"]) == 2


# SQLiteStorage Tests
class TestSQLiteStorage:
    def test_init_creates_table(self, temp_db_path):
        """Test that initialization creates the required table."""
        # Create storage
        storage = SQLiteStorage(db_path=temp_db_path)
        
        # Check if table exists
        with sqlite3.connect(temp_db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='workflow_states'")
            result = cursor.fetchone()
            
        assert result is not None
        assert result[0] == "workflow_states"
    
    def test_save_and_load_state(self, sqlite_storage, sample_state):
        """Test basic save and load functionality."""
        workflow_id = "test.workflow"
        run_id = "test_run_1"
        
        # Save state
        sqlite_storage.save_state(workflow_id, run_id, sample_state)
        
        # Load state
        loaded_state = sqlite_storage.load_state(workflow_id, run_id)
        
        # Verify state was properly saved and loaded
        assert loaded_state == sample_state
    
    def test_load_nonexistent_state(self, sqlite_storage):
        """Test loading a non-existent workflow state."""
        loaded_state = sqlite_storage.load_state("nonexistent", "nonexistent")
        assert loaded_state is None
    
    def test_state_update(self, sqlite_storage, sample_state):
        """Test updating an existing state."""
        workflow_id = "test.workflow"
        run_id = "test_run"
        
        # Save initial state
        sqlite_storage.save_state(workflow_id, run_id, sample_state)
        
        # Update state
        updated_state = sample_state.copy()
        updated_state["steps"].append({
            "shared": {"key": "updated"},
            "next_node_id": "node2",
            "workflow_status": "RUNNING",
            "node_statuses": {"node1": "completed"},
            "awaiting_input": None,
            "previous_node_id": "node1",
            "metadata": {"step": 2}
        })
        
        # Save updated state
        sqlite_storage.save_state(workflow_id, run_id, updated_state)
        
        # Load state
        loaded_state = sqlite_storage.load_state(workflow_id, run_id)
        
        # Verify state was updated
        assert loaded_state == updated_state
        assert len(loaded_state["steps"]) == 2
    
    # Additional tests for list_runs and list_workflows for SQLite
    # Since these methods aren't shown in the code snippet, I'll implement them
    # based on what would be expected similar to FileSystemStorage
    
    def test_list_runs(self, sqlite_storage, sample_state, temp_db_path):
        """Test listing runs for a workflow."""
        workflow_id = "test.workflow"
        run_ids = ["run_1", "run_2", "run_3"]
        
        # Create multiple runs
        for run_id in run_ids:
            sqlite_storage.save_state(workflow_id, run_id, sample_state)
        
        # Implement a basic list_runs method for testing
        with sqlite3.connect(temp_db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT run_id FROM workflow_states WHERE workflow_id = ? ORDER BY updated_at DESC",
                (workflow_id,)
            )
            listed_runs = [row[0] for row in cursor.fetchall()]
        
        # Verify all runs are listed
        assert set(listed_runs) == set(run_ids)
    
    def test_list_workflows(self, sqlite_storage, sample_state, temp_db_path):
        """Test listing all workflows."""
        workflow_ids = ["test.workflow1", "test.workflow2", "test.workflow3"]
        run_id = "run_1"
        
        # Create multiple workflows
        for workflow_id in workflow_ids:
            sqlite_storage.save_state(workflow_id, run_id, sample_state)
        
        # Implement a basic list_workflows method for testing
        with sqlite3.connect(temp_db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT DISTINCT workflow_id FROM workflow_states"
            )
            listed_workflows = [row[0] for row in cursor.fetchall()]
        
        # Verify all workflows are listed
        assert set(listed_workflows) == set(workflow_ids)


# Edge Cases Tests
class TestStorageEdgeCases:
    @pytest.mark.parametrize("storage_fixture", ["fs_storage", "sqlite_storage"])
    def test_empty_state(self, request, storage_fixture):
        """Test saving and loading an empty state."""
        storage = request.getfixturevalue(storage_fixture)
        workflow_id = "test.workflow"
        run_id = "empty_run"
        empty_state = {"steps": []}
        
        # Save empty state
        storage.save_state(workflow_id, run_id, empty_state)
        
        # Load state
        loaded_state = storage.load_state(workflow_id, run_id)
        
        # Verify empty state was properly saved and loaded
        assert loaded_state == empty_state
    
    @pytest.mark.parametrize("storage_fixture", ["fs_storage", "sqlite_storage"])
    def test_large_state(self, request, storage_fixture):
        """Test saving and loading a large state."""
        storage = request.getfixturevalue(storage_fixture)
        workflow_id = "test.workflow"
        run_id = "large_run"
        
        # Create a large state
        large_state = {
            "workflow_id": workflow_id,
            "run_id": run_id,
            "steps": [
                {
                    "shared": {"data": "x" * 1000},  # 1KB of data
                    "next_node_id": f"node{i}",
                    "workflow_status": "RUNNING",
                    "node_statuses": {f"node{j}": "completed" for j in range(i)},
                    "awaiting_input": None,
                    "previous_node_id": f"node{i-1}" if i > 0 else None,
                    "metadata": {"step": i}
                }
                for i in range(100)  # 100 steps
            ]
        }
        
        # Save large state
        storage.save_state(workflow_id, run_id, large_state)
        
        # Load state
        loaded_state = storage.load_state(workflow_id, run_id)
        
        # Verify large state was properly saved and loaded
        assert loaded_state == large_state
        assert len(loaded_state["steps"]) == 100
    
    @pytest.mark.parametrize("storage_fixture", ["fs_storage", "sqlite_storage"])
    def test_special_characters(self, request, storage_fixture):
        """Test saving and loading state with special characters."""
        storage = request.getfixturevalue(storage_fixture)
        workflow_id = "test.workflow-with_special!chars"
        run_id = "run-with_special!chars"
        state = {
            "workflow_id": workflow_id,
            "run_id": run_id,
            "steps": [
                {
                    "shared": {"key": "value with spaces and symbols !@#$%^&*()_+"},
                    "next_node_id": "node1",
                    "workflow_status": "HEALTHY",
                    "node_statuses": {"start": "completed"},
                    "awaiting_input": None,
                    "previous_node_id": "start",
                    "metadata": {"step": 1}
                }
            ]
        }
        
        # Save state with special characters
        storage.save_state(workflow_id, run_id, state)
        
        # Load state
        loaded_state = storage.load_state(workflow_id, run_id)
        
        # Verify state was properly saved and loaded
        assert loaded_state == state

