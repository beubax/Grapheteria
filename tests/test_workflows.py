import pytest
import asyncio
import os
import json
import tempfile
from unittest.mock import patch, MagicMock
from datetime import datetime

from grapheteria import (
    WorkflowEngine, Node, WorkflowStatus, NodeStatus, 
    ExecutionState, StorageBackend, FileSystemStorage
)

# Custom Node classes for testing
class StartNode(Node):
    def execute(self, prepared_result):
        return {"message": "Started"}
    
    def cleanup(self, shared, prepared_result, execution_result):
        shared["start_executed"] = True
        return execution_result

class ProcessNode(Node):
    def execute(self, prepared_result):
        return {"message": "Processed"}
    
    def cleanup(self, shared, prepared_result, execution_result):
        shared["process_executed"] = True
        return execution_result

class InputNode(Node):
    def prepare(self, shared, request_input):
        return request_input("What's your name?", input_type="text")
    
    def execute(self, user_input):
        return {"user_name": user_input}
    
    def cleanup(self, shared, prepared_result, execution_result):
        shared["user_name"] = execution_result["user_name"]
        return execution_result

class EndNode(Node):
    def execute(self, prepared_result):
        return {"message": "Completed"}
    
    def cleanup(self, shared, prepared_result, execution_result):
        shared["end_executed"] = True
        return execution_result

class FailingNode(Node):
    def execute(self, prepared_result):
        raise ValueError("This node intentionally fails")


# Test fixtures
@pytest.fixture
def nodes():
    start = StartNode(id="start")
    process = ProcessNode(id="process")
    end = EndNode(id="end")
    
    # Connect nodes
    start > process > end
    
    return [start, process, end]

@pytest.fixture
def nodes_with_input():
    start = StartNode(id="start")
    input_node = InputNode(id="input")
    end = EndNode(id="end")
    
    # Connect nodes
    start > input_node > end
    
    return [start, input_node, end]

@pytest.fixture
def workflow_json():
    """Create a temporary workflow JSON file."""
    with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as tmp:
        workflow_data = {
            "nodes": [
                {"id": "start", "class": "StartNode", "config": {}},
                {"id": "process", "class": "ProcessNode", "config": {}},
                {"id": "end", "class": "EndNode", "config": {}}
            ],
            "edges": [
                {"from": "start", "to": "process"},
                {"from": "process", "to": "end"}
            ],
            "start": "start",
            "initial_state": {"counter": 0}
        }
        tmp.write(json.dumps(workflow_data).encode())
        tmp_path = tmp.name
    
    yield tmp_path
    # Clean up
    if os.path.exists(tmp_path):
        os.unlink(tmp_path)


# Tests for initialization
class TestInitialization:
    
    @pytest.mark.asyncio
    async def test_init_with_nodes(self, nodes):
        """Test initializing WorkflowEngine with code-based nodes."""
        engine = WorkflowEngine(nodes=nodes, start=nodes[0])
        
        assert engine.workflow_id is not None
        assert engine.nodes is not None
        assert engine.start_node_id == "start"
        assert engine.run_id is not None
        assert engine.execution_state.workflow_status == WorkflowStatus.HEALTHY
        
    @pytest.mark.asyncio
    async def test_init_with_json(self, workflow_json):
        """Test initializing WorkflowEngine with JSON file."""
        engine = WorkflowEngine(workflow_path=workflow_json)
        
        assert engine.workflow_id is not None
        assert engine.nodes is not None
        assert engine.start_node_id == "start"
        assert engine.run_id is not None
        
    @pytest.mark.asyncio
    async def test_init_with_workflow_id(self, workflow_json):
        """Test initializing with workflow_id instead of path."""
        # Mock the id_to_path function to return our temp file
        with patch('grapheteria.id_to_path', return_value=workflow_json):
            engine = WorkflowEngine(workflow_id="test.workflow")
            
            assert engine.workflow_id == "test.workflow"
            assert engine.nodes is not None
    
    @pytest.mark.asyncio
    async def test_default_start_node(self, nodes):
        """Test that first node is used as start if not specified."""
        engine = WorkflowEngine(nodes=nodes)
        
        assert engine.start_node_id == "start"
        
    @pytest.mark.asyncio
    async def test_explicit_start_node(self, nodes):
        """Test setting a specific start node."""
        engine = WorkflowEngine(nodes=nodes, start=nodes[1])
        
        assert engine.start_node_id == "process"
        
    @pytest.mark.asyncio
    async def test_initial_shared_state(self, nodes):
        """Test setting initial shared state."""
        initial_state = {"counter": 42, "name": "test"}
        engine = WorkflowEngine(nodes=nodes, initial_shared_state=initial_state)
        
        assert engine.execution_state.shared == initial_state
        
    @pytest.mark.asyncio
    async def test_missing_workflow(self):
        """Test error when no workflow source is provided."""
        with pytest.raises(ValueError):
            WorkflowEngine()


# Tests for run ID and resumption
class TestRunIdAndResumption:
    
    @pytest.mark.asyncio
    async def test_run_id_generation(self, nodes):
        """Test that a run_id is automatically generated."""
        engine = WorkflowEngine(nodes=nodes)
        
        # Check that run_id looks like a timestamp
        assert isinstance(engine.run_id, str)
        assert len(engine.run_id) > 10  # Just a sanity check for length
        
    @pytest.mark.asyncio
    async def test_resume_workflow(self, nodes):
        """Test resuming a workflow from a previous run_id."""
        # Mock the storage backend to return a valid state
        mock_storage = MagicMock(spec=StorageBackend)
        mock_state = {
            "workflow_id": "test",
            "run_id": "test_run",
            "steps": [
                {
                    "shared": {"start_executed": True},
                    "next_node_id": "process",
                    "workflow_status": "HEALTHY",
                    "node_statuses": {"start": "completed"},
                    "awaiting_input": None,
                    "previous_node_id": "start",
                    "metadata": {}
                }
            ]
        }
        mock_storage.load_state.return_value = mock_state
        
        engine = WorkflowEngine(
            workflow_id="test",
            run_id="test_run",
            nodes=nodes,
            storage_backend=mock_storage
        )
        
        assert engine.run_id == "test_run"
        assert engine.execution_state.next_node_id == "process"
        assert engine.execution_state.shared == {"start_executed": True}
        
    @pytest.mark.asyncio
    async def test_resume_non_existent_run(self, nodes):
        """Test error when trying to resume a non-existent run."""
        mock_storage = MagicMock(spec=StorageBackend)
        mock_storage.load_state.return_value = None
        
        with pytest.raises(FileNotFoundError):
            WorkflowEngine(
                workflow_id="test",
                run_id="nonexistent_run",
                nodes=nodes,
                storage_backend=mock_storage
            )
    
    @pytest.mark.asyncio
    async def test_fork_workflow(self, nodes):
        """Test forking a workflow from a previous run."""
        # Mock the storage backend to return a valid state
        mock_storage = MagicMock(spec=StorageBackend)
        mock_state = {
            "workflow_id": "test",
            "run_id": "test_run",
            "steps": [
                {
                    "shared": {"start_executed": True},
                    "next_node_id": "process",
                    "workflow_status": "HEALTHY",
                    "node_statuses": {"start": "completed"},
                    "awaiting_input": None,
                    "previous_node_id": "start",
                    "metadata": {}
                }
            ]
        }
        mock_storage.load_state.return_value = mock_state
        
        engine = WorkflowEngine(
            workflow_id="test",
            run_id="test_run",
            nodes=nodes,
            storage_backend=mock_storage,
            fork=True
        )
        
        # Should have a new run_id
        assert engine.run_id != "test_run"
        # But should have the state from the original run
        assert engine.execution_state.next_node_id == "process"


# Tests for execution state
class TestExecutionState:
    
    @pytest.mark.asyncio
    async def test_execution_state_initial(self, nodes):
        """Test initial execution state."""
        engine = WorkflowEngine(nodes=nodes)
        
        assert engine.execution_state.next_node_id == "start"
        assert engine.execution_state.workflow_status == WorkflowStatus.HEALTHY
        assert engine.execution_state.shared == {}
        assert engine.execution_state.awaiting_input is None
        
    @pytest.mark.asyncio
    async def test_execution_state_after_step(self, nodes):
        """Test execution state after a step."""
        engine = WorkflowEngine(nodes=nodes)
        
        continuing, _ = await engine.step()
        
        assert continuing is True
        assert engine.execution_state.previous_node_id == "start"
        assert engine.execution_state.next_node_id == "process"
        assert engine.execution_state.shared == {"start_executed": True}
        assert "start" in engine.execution_state.node_statuses
        assert engine.execution_state.node_statuses["start"] == NodeStatus.COMPLETED


# Tests for input handling
class TestInputHandling:
    
    @pytest.mark.asyncio
    async def test_awaiting_input(self, nodes_with_input):
        """Test workflow pausing for input."""
        engine = WorkflowEngine(nodes=nodes_with_input)
        
        # Run until we hit the input node
        continuing, _ = await engine.run()
        
        assert continuing is True
        assert engine.execution_state.workflow_status == WorkflowStatus.WAITING_FOR_INPUT
        assert engine.execution_state.awaiting_input is not None
        assert engine.execution_state.awaiting_input['node_id'] == "input"
        assert engine.execution_state.awaiting_input['prompt'] == "What's your name?"
        
    @pytest.mark.asyncio
    async def test_providing_input(self, nodes_with_input):
        """Test providing input to a waiting workflow."""
        engine = WorkflowEngine(nodes=nodes_with_input)
        
        # Run until we hit the input node
        continuing, _ = await engine.run()
        
        # Now provide the requested input
        continuing, _ = await engine.step({"input": "Alice"})
        
        # Input should be processed and workflow should continue
        assert engine.execution_state.shared.get("user_name") == "Alice"
        assert engine.execution_state.awaiting_input is None


# Tests for step and run functions
class TestExecution:
    
    @pytest.mark.asyncio
    async def test_step_execution(self, nodes):
        """Test executing a single step."""
        engine = WorkflowEngine(nodes=nodes)
        
        # Execute first node
        continuing, _ = await engine.step()
        
        assert continuing is True
        assert engine.execution_state.shared == {"start_executed": True}
        assert engine.execution_state.next_node_id == "process"
        
        # Execute second node
        continuing, _ = await engine.step()
        
        assert continuing is True
        assert engine.execution_state.shared == {"start_executed": True, "process_executed": True}
        assert engine.execution_state.next_node_id == "end"
        
    @pytest.mark.asyncio
    async def test_run_execution(self, nodes):
        """Test executing the entire workflow."""
        engine = WorkflowEngine(nodes=nodes)
        
        # Run the whole workflow
        continuing, _ = await engine.run()
        
        assert continuing is False  # Workflow should be complete
        assert engine.execution_state.workflow_status == WorkflowStatus.COMPLETED
        assert engine.execution_state.shared == {
            "start_executed": True, 
            "process_executed": True,
            "end_executed": True
        }
        
    @pytest.mark.asyncio
    async def test_step_with_input(self, nodes_with_input):
        """Test stepping through a workflow with input."""
        engine = WorkflowEngine(nodes=nodes_with_input)
        
        # First step (start node)
        continuing, _ = await engine.step()
        assert continuing is True
        
        # Second step (input node) - will wait for input
        continuing, _ = await engine.step()
        assert continuing is True
        assert engine.execution_state.awaiting_input is not None
        
        # Provide input
        continuing, _ = await engine.step({"input": "Bob"})
        assert continuing is True
        assert engine.execution_state.shared.get("user_name") == "Bob"
        
        # Final step (end node)
        continuing, _ = await engine.step()
        assert continuing is False
        assert engine.execution_state.workflow_status == WorkflowStatus.COMPLETED
        
    @pytest.mark.asyncio
    async def test_run_with_input(self, nodes_with_input):
        """Test running a workflow with input."""
        engine = WorkflowEngine(nodes=nodes_with_input)
        
        # Run until input is needed
        continuing, _ = await engine.run()
        assert continuing is True
        assert engine.execution_state.awaiting_input is not None
        
        # Provide input and complete the workflow
        continuing, _ = await engine.run({"input": "Charlie"})
        assert continuing is False
        assert engine.execution_state.workflow_status == WorkflowStatus.COMPLETED
        assert engine.execution_state.shared.get("user_name") == "Charlie"


# Edge cases and error handling
class TestEdgeCases:
    
    @pytest.mark.asyncio
    async def test_failing_node(self):
        """Test workflow handling a node that raises an exception."""
        failing_node = FailingNode(id="failing")
        end_node = EndNode(id="end")
        
        failing_node > end_node
        
        engine = WorkflowEngine(nodes=[failing_node, end_node])
        
        # The node should fail and the workflow should be marked as failed
        with pytest.raises(ValueError):
            await engine.step()
        
        assert engine.execution_state.workflow_status == WorkflowStatus.FAILED
        assert engine.execution_state.node_statuses.get("failing") == NodeStatus.FAILED
        
    @pytest.mark.asyncio
    async def test_step_completed_workflow(self, nodes):
        """Test stepping a workflow that's already complete."""
        engine = WorkflowEngine(nodes=nodes)
        
        # Run to completion
        continuing, _ = await engine.run()
        assert continuing is False
        
        # Try to step again
        continuing, _ = await engine.step()
        assert continuing is False  # Should still be complete
        
    @pytest.mark.asyncio
    async def test_input_on_non_waiting_workflow(self, nodes):
        """Test providing input when none is requested."""
        engine = WorkflowEngine(nodes=nodes)
        
        # Provide input when none is needed
        continuing, _ = await engine.step({"input": "Should be ignored"})
        
        # Workflow should continue normally
        assert engine.execution_state.next_node_id == "process"
        
    @pytest.mark.asyncio
    async def test_wrong_input_key(self, nodes_with_input):
        """Test providing input with wrong key."""
        engine = WorkflowEngine(nodes=nodes_with_input)
        
        # Run until input is needed
        continuing, _ = await engine.run()
        
        # Provide input with wrong key
        continuing, _ = await engine.step({"wrong_key": "Alice"})
        
        # Should still be waiting for input
        assert engine.execution_state.workflow_status == WorkflowStatus.WAITING_FOR_INPUT
        assert engine.execution_state.awaiting_input is not None