from time import sleep
import pytest
import os
import tempfile
import shutil
from pathlib import Path
from unittest.mock import patch, MagicMock

from grapheteria import (
    Node, WorkflowEngine, WorkflowStatus, NodeStatus, 
    ExecutionState
)
from grapheteria.utils import FileSystemStorage, SQLiteStorage

# Custom Node classes for testing
class StartNode(Node):
    async def execute(self, prepared_result):
        return {"message": "Started"}
    
    def cleanup(self, shared, prepared_result, execution_result):
        shared["start_result"] = execution_result
        return execution_result

class ProcessNode(Node):
    async def execute(self, prepared_result):
        return {"message": "Processed"}
    
    def cleanup(self, shared, prepared_result, execution_result):
        shared["process_result"] = execution_result
        return execution_result

class InputNode(Node):
    def prepare(self, shared, request_input):
        self.request_input = request_input
        return shared
        
    async def execute(self, prepared_result):
        user_input = await self.request_input(prompt="Enter value:", options=None, input_type="text")
        return {"user_input": user_input}
    
    def cleanup(self, shared, prepared_result, execution_result):
        shared["user_input"] = execution_result
        return execution_result

class EndNode(Node):
    async def execute(self, prepared_result):
        return {"message": "Completed"}
    
    def cleanup(self, shared, prepared_result, execution_result):
        shared["end_result"] = execution_result
        return execution_result

# Fixtures
@pytest.fixture
def temp_log_dir():
    """Create a temporary directory for logs"""
    temp_dir = tempfile.mkdtemp()
    yield temp_dir
    shutil.rmtree(temp_dir)

@pytest.fixture
def temp_db_path():
    """Create a temporary SQLite database path"""
    fd, path = tempfile.mkstemp(suffix='.db')
    os.close(fd)
    yield path
    os.unlink(path)

@pytest.fixture
def basic_workflow():
    """Create a basic workflow with three nodes"""
    start_node = StartNode()
    process_node = ProcessNode()
    end_node = EndNode()
    
    # Connect nodes
    start_node > process_node > end_node
    
    return [start_node, process_node, end_node], start_node

@pytest.fixture
def workflow_with_input():
    """Create a workflow with an input node"""
    start_node = StartNode()
    input_node = InputNode()
    end_node = EndNode()
    
    # Connect nodes
    start_node > input_node > end_node
    
    return [start_node, input_node, end_node], start_node

# Tests for Run ID Generation
async def test_run_id_generation(temp_log_dir, basic_workflow):
    """Test that a unique run ID is generated when creating a workflow"""
    nodes, start = basic_workflow
    
    engine = WorkflowEngine(
        nodes=nodes,
        start=start,
        storage_backend=FileSystemStorage(base_dir=temp_log_dir)
    )
    
    # Verify run_id format (timestamp pattern)
    assert engine.run_id is not None
    assert len(engine.run_id) > 10  # Should be substantial in length
    
    # Run the workflow to completion
    continuing = await engine.run()
    assert not continuing  # Workflow should complete

# Tests for Basic Workflow Resumption
async def test_basic_workflow_resumption(temp_log_dir, basic_workflow):
    """Test resuming a workflow from its most recent state"""
    nodes, start = basic_workflow
    
    # Create and run the initial workflow
    engine = WorkflowEngine(
        nodes=nodes,
        start=start,
        storage_backend=FileSystemStorage(base_dir=temp_log_dir)
    )
    
    run_id = engine.run_id
    workflow_id = engine.workflow_id
    
    # Run the workflow partially (just one step)
    await engine.step()
    
    # Resume the workflow
    resumed_engine = WorkflowEngine(
        workflow_id=workflow_id,
        run_id=run_id,
        nodes=nodes,
        storage_backend=FileSystemStorage(base_dir=temp_log_dir)
    )
    
    # Check that the state was properly loaded
    assert resumed_engine.execution_state.shared.get("start_result") is not None
    assert resumed_engine.execution_state.next_node_id == engine.execution_state.next_node_id
    
    # Complete the workflow
    continuing = await resumed_engine.run()
    assert not continuing  # Workflow should complete
    assert resumed_engine.execution_state.workflow_status == WorkflowStatus.COMPLETED
    
    # Check all nodes executed
    assert "start_result" in resumed_engine.execution_state.shared
    assert "process_result" in resumed_engine.execution_state.shared
    assert "end_result" in resumed_engine.execution_state.shared

# Tests for Resuming from Specific Step
async def test_resume_from_specific_step(temp_log_dir, basic_workflow):
    """Test resuming a workflow from a specific step"""
    nodes, start = basic_workflow
    
    # Create and run the initial workflow
    engine = WorkflowEngine(
        nodes=nodes,
        start=start,
        storage_backend=FileSystemStorage(base_dir=temp_log_dir)
    )
    
    run_id = engine.run_id
    workflow_id = engine.workflow_id
    
    # Run the workflow to completion
    continuing = await engine.run()
    assert not continuing
    
    # Resume from step 1 (after start node)
    resumed_engine = WorkflowEngine(
        workflow_id=workflow_id,
        run_id=run_id,
        nodes=nodes,
        resume_from=1,  # Resume from step 1
        storage_backend=FileSystemStorage(base_dir=temp_log_dir)
    )
    
    # Clear the shared state for testing
    resumed_engine.execution_state.shared = {"start_result": resumed_engine.execution_state.shared["start_result"]}
    
    # Complete the workflow
    continuing = await resumed_engine.run()
    assert not continuing
    
    # Verify only the remaining nodes executed
    assert "start_result" in resumed_engine.execution_state.shared
    assert "process_result" in resumed_engine.execution_state.shared
    assert "end_result" in resumed_engine.execution_state.shared

# Tests for Forking Workflows
async def test_workflow_forking(temp_log_dir, basic_workflow):
    """Test forking a workflow from a previous run"""
    nodes, start = basic_workflow
    
    # Create and run the initial workflow
    engine = WorkflowEngine(
        nodes=nodes,
        start=start,
        storage_backend=FileSystemStorage(base_dir=temp_log_dir)
    )
    
    original_run_id = engine.run_id
    workflow_id = engine.workflow_id
    
    # Run first step
    await engine.step()
    
    # Fork from the first step
    forked_engine = WorkflowEngine(
        workflow_id=workflow_id,
        run_id=original_run_id,
        nodes=nodes,
        resume_from=0,
        fork=True,
        storage_backend=FileSystemStorage(base_dir=temp_log_dir)
    )

    #Since this runs very quickly, let's sleep for a second to generate a new run_id
    sleep(2)
    
    # Verify it's a new run with forked metadata
    assert forked_engine.run_id != original_run_id
    assert "forked_from" in forked_engine.tracking_data
    assert forked_engine.tracking_data["forked_from"] == original_run_id

    # Complete the original workflow
    continuing = await engine.run()
    assert not continuing
    
    # Complete the forked workflow
    continuing = await forked_engine.run()
    assert not continuing
    
    # Both workflows should have completed successfully
    storage = FileSystemStorage(base_dir=temp_log_dir)
    original_state = storage.load_state(workflow_id, original_run_id)
    forked_state = storage.load_state(workflow_id, forked_engine.run_id)
    
    assert original_state is not None
    assert forked_state is not None
    assert len(forked_state["steps"]) > 0

# Tests for State Validation
async def test_state_validation_failure(temp_log_dir, basic_workflow):
    """Test that validation fails when required nodes are missing"""
    nodes, start = basic_workflow
    
    # Create and run the initial workflow
    engine = WorkflowEngine(
        nodes=nodes,
        start=start,
        storage_backend=FileSystemStorage(base_dir=temp_log_dir)
    )
    
    run_id = engine.run_id
    workflow_id = engine.workflow_id
    
    # Run first step
    await engine.step()
    
    # Try to resume with incomplete nodes list (missing process_node)
    with pytest.raises(ValueError, match="missing from current workflow"):
        # Only include start_node and end_node
        incomplete_nodes = [StartNode(), EndNode()]
        WorkflowEngine(
            workflow_id=workflow_id,
            run_id=run_id,
            nodes=incomplete_nodes,
            start=incomplete_nodes[0],
            storage_backend=FileSystemStorage(base_dir=temp_log_dir)
        )

# Tests for Input Handling and Resumption
async def test_input_handling_and_resumption(temp_log_dir, workflow_with_input):
    """Test workflow with input request and resumption"""
    nodes, start = workflow_with_input
    
    # Create workflow
    engine = WorkflowEngine(
        nodes=nodes,
        start=start,
        storage_backend=FileSystemStorage(base_dir=temp_log_dir)
    )
    
    run_id = engine.run_id
    workflow_id = engine.workflow_id
    
    # Run until input is needed
    continuing = await engine.run()
    assert engine.execution_state.workflow_status == WorkflowStatus.WAITING_FOR_INPUT
    assert engine.execution_state.awaiting_input is not None
    
    # Get the request ID
    request_id = engine.execution_state.awaiting_input["request_id"]
    print(request_id)
    
    # Resume the workflow in a new instance
    resumed_engine = WorkflowEngine(
        workflow_id=workflow_id,
        nodes=nodes,
        run_id=run_id,
        storage_backend=FileSystemStorage(base_dir=temp_log_dir)
    )
    
    print(resumed_engine.execution_state.awaiting_input)
    # Verify input state was preserved
    assert resumed_engine.execution_state.workflow_status == WorkflowStatus.WAITING_FOR_INPUT
    assert resumed_engine.execution_state.awaiting_input is not None
    
    # Provide input and continue
    continuing = await resumed_engine.run({request_id: "test_input"})
    assert not continuing  # Workflow should complete
    
    # Verify input was processed
    assert resumed_engine.execution_state.shared.get("user_input", {}).get("user_input") == "test_input"
    assert resumed_engine.execution_state.workflow_status == WorkflowStatus.COMPLETED

# Tests for Different Storage Backends
async def test_sqlite_storage_backend(temp_db_path, basic_workflow):
    """Test using SQLite storage backend"""
    nodes, start = basic_workflow
    
    # Create workflow with SQLite storage
    engine = WorkflowEngine(
        nodes=nodes,
        start=start,
        storage_backend=SQLiteStorage(db_path=temp_db_path)
    )
    
    run_id = engine.run_id
    workflow_id = engine.workflow_id
    
    # Run workflow
    continuing = await engine.run()
    assert not continuing
    
    # Resume workflow from SQLite
    resumed_engine = WorkflowEngine(
        workflow_id=workflow_id,
        nodes=nodes,
        run_id=run_id,
        storage_backend=SQLiteStorage(db_path=temp_db_path)
    )
    
    # Verify state was properly loaded
    assert resumed_engine.execution_state.workflow_status == WorkflowStatus.COMPLETED
    assert "start_result" in resumed_engine.execution_state.shared
    assert "process_result" in resumed_engine.execution_state.shared
    assert "end_result" in resumed_engine.execution_state.shared

# Edge Cases
async def test_resume_nonexistent_run(temp_log_dir, basic_workflow):
    """Test resuming a non-existent run ID"""
    nodes, start = basic_workflow
    
    with pytest.raises(FileNotFoundError, match="No state found for run_id"):
        WorkflowEngine(
            workflow_id="test_workflow",
            nodes=nodes,
            run_id="non_existent_run_id",
            storage_backend=FileSystemStorage(base_dir=temp_log_dir)
        )

async def test_resume_from_invalid_step(temp_log_dir, basic_workflow):
    """Test resuming from an invalid step number"""
    nodes, start = basic_workflow
    
    # Create and run workflow
    engine = WorkflowEngine(
        nodes=nodes,
        start=start,
        storage_backend=FileSystemStorage(base_dir=temp_log_dir)
    )
    
    run_id = engine.run_id
    workflow_id = engine.workflow_id
    
    # Run the workflow to completion
    continuing = await engine.run()
    
    # Try resuming from a non-existent step
    with pytest.raises(ValueError, match="Step .* not found"):
        WorkflowEngine(
            workflow_id=workflow_id,
            run_id=run_id,
            nodes=nodes,
            resume_from=999,  # Invalid step number
            storage_backend=FileSystemStorage(base_dir=temp_log_dir)
        )