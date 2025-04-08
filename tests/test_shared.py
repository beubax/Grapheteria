import pytest
import asyncio
import json
import os
import tempfile
from unittest.mock import MagicMock, patch

from grapheteria import Node, WorkflowEngine, ExecutionState, WorkflowStatus


# Test Node implementations
class ReadNode(Node):
    """Node that reads from shared state"""
    def prepare(self, shared, request_input):
        self.read_value = shared.get('test_key', None)
        return self.read_value
        
    def execute(self, prepared_result):
        return prepared_result
        
    def cleanup(self, shared, prepared_result, execution_result):
        shared['read_node_processed'] = True
        return execution_result


class WriteNode(Node):
    """Node that writes to shared state"""
    def prepare(self, shared, request_input):
        return self.config.get('value_to_write', 'default_value')
        
    def execute(self, prepared_result):
        return prepared_result
        
    def cleanup(self, shared, prepared_result, execution_result):
        shared['test_key'] = execution_result
        return execution_result


class ModifyNode(Node):
    """Node that modifies existing shared state"""
    def prepare(self, shared, request_input):
        return shared.get('test_key', None)
        
    def execute(self, prepared_result):
        if prepared_result is None:
            return None
        return prepared_result + "_modified"
        
    def cleanup(self, shared, prepared_result, execution_result):
        if execution_result is not None:
            shared['test_key'] = execution_result
        return execution_result


class ListAppendNode(Node):
    """Node that appends to a list in shared state"""
    def prepare(self, shared, request_input):
        self.items = shared.get('items', [])
        return self.config.get('item_to_append', 'default_item')
        
    def execute(self, prepared_result):
        return prepared_result
        
    def cleanup(self, shared, prepared_result, execution_result):
        if 'items' not in shared:
            shared['items'] = []
        shared['items'].append(execution_result)
        return execution_result


class NonSerializableNode(Node):
    """Node that attempts to add non-serializable data to shared state"""
    def prepare(self, shared, request_input):
        return "data"
        
    def execute(self, prepared_result):
        # Create something that can't be JSON serialized
        from threading import Lock
        return Lock()
        
    def cleanup(self, shared, prepared_result, execution_result):
        # This will cause serialization issues
        shared['non_serializable'] = execution_result
        return execution_result


# Fixtures
@pytest.fixture
def temp_workflow_dir():
    """Create a temporary directory for workflow files"""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield tmpdir


# Test cases
class TestSharedDictionary:
    
    @pytest.mark.asyncio
    async def test_basic_read_write(self):
        """Test basic reading and writing to shared dictionary"""
        # Create workflow
        write_node = WriteNode(id="write", config={"value_to_write": "test_value"})
        read_node = ReadNode(id="read")
        write_node > read_node  # Connect nodes
        
        workflow = WorkflowEngine(
            nodes=[write_node, read_node],
            start=write_node
        )
        
        # Run the workflow
        continuing, tracking_data = await workflow.run()
        
        # Verify the shared state contains our values
        assert not continuing  # Workflow should be complete
        assert tracking_data['steps'][-1]['shared']['test_key'] == "test_value"
        assert tracking_data['steps'][-1]['shared']['read_node_processed'] == True
    
    @pytest.mark.asyncio
    async def test_initial_state(self):
        """Test setting initial state in the workflow"""
        # Create a simple node that will read from initial state
        read_node = ReadNode(id="read")
        
        # Create workflow with initial shared state
        workflow = WorkflowEngine(
            nodes=[read_node],
            start=read_node,
            initial_shared_state={"test_key": "initial_value", "items": [1, 2, 3]}
        )
        
        # Run the workflow
        continuing, tracking_data = await workflow.run()
        
        # Verify the shared state contains our initial values
        assert not continuing  # Workflow should be complete
        final_state = tracking_data['steps'][-1]['shared']
        assert final_state['test_key'] == "initial_value"
        assert final_state['items'] == [1, 2, 3]
        assert final_state['read_node_processed'] == True
    
    @pytest.mark.asyncio
    async def test_sequential_modification(self):
        """Test sequential modification of the shared state"""
        # Create nodes that will modify state in sequence
        write_node = WriteNode(id="write", config={"value_to_write": "original"})
        modify_node = ModifyNode(id="modify")
        read_node = ReadNode(id="read")
        
        # Connect in sequence
        write_node > modify_node > read_node
        
        workflow = WorkflowEngine(
            nodes=[write_node, modify_node, read_node],
            start=write_node
        )
        
        # Run the workflow
        continuing, tracking_data = await workflow.run()
        
        # Verify the changes through the chain
        assert not continuing
        steps = tracking_data['steps']
        
        # First step (after write_node)
        assert steps[1]['shared']['test_key'] == "original"
        
        # Second step (after modify_node)
        assert steps[2]['shared']['test_key'] == "original_modified"
        
        # Final state should maintain the modified value
        assert steps[-1]['shared']['test_key'] == "original_modified"
    
    @pytest.mark.asyncio
    async def test_list_append_operations(self):
        """Test appending to a list in shared state"""
        # Create a workflow that appends to a list
        append1 = ListAppendNode(id="append1", config={"item_to_append": "item1"})
        append2 = ListAppendNode(id="append2", config={"item_to_append": "item2"})
        append3 = ListAppendNode(id="append3", config={"item_to_append": "item3"})
        
        # Connect nodes
        append1 > append2 > append3
        
        workflow = WorkflowEngine(
            nodes=[append1, append2, append3],
            start=append1,
            initial_shared_state={"items": ["initial_item"]}
        )
        
        # Run the workflow
        continuing, tracking_data = await workflow.run()
        
        # Check the final list
        assert not continuing
        final_state = tracking_data['steps'][-1]['shared']
        assert final_state['items'] == ["initial_item", "item1", "item2", "item3"]
    
    @pytest.mark.asyncio
    async def test_empty_shared_state(self):
        """Test handling of empty shared state"""
        # Create a node that tries to read from nonexistent key
        read_node = ReadNode(id="read")
        
        workflow = WorkflowEngine(
            nodes=[read_node],
            start=read_node
            # No initial state provided
        )
        
        # Run the workflow
        continuing, tracking_data = await workflow.run()
        
        # Verify behavior with empty state
        assert not continuing
        final_state = tracking_data['steps'][-1]['shared']
        assert 'read_node_processed' in final_state
        assert final_state['read_node_processed'] == True
        assert 'test_key' not in final_state  # The key wasn't created
    
    @pytest.mark.asyncio
    async def test_state_persistence(self, temp_workflow_dir):
        """Test that shared state is properly persisted between steps"""
        write_node = WriteNode(id="write", config={"value_to_write": "persistent_value"})
        
        # Create a workflow with file system storage
        workflow = WorkflowEngine(
            nodes=[write_node],
            start=write_node
        )
        
        # Run the workflow
        continuing, tracking_data = await workflow.run()
        
        # Grab the run_id
        run_id = tracking_data['run_id']
        workflow_id = tracking_data['workflow_id']
        
        # Create a new workflow engine that loads the existing run
        resumed_workflow = WorkflowEngine(
            workflow_id=workflow_id,
            run_id=run_id,
            nodes=[write_node]
        )
        
        # Check that the shared state was loaded correctly
        loaded_state = resumed_workflow.execution_state.shared
        assert 'test_key' in loaded_state
        assert loaded_state['test_key'] == "persistent_value"
    
    @pytest.mark.asyncio
    async def test_serialization_error(self):
        """Test handling of non-serializable objects in shared state"""
        non_serializable_node = NonSerializableNode(id="non_serializable")
        
        workflow = WorkflowEngine(
            nodes=[non_serializable_node],
            start=non_serializable_node
        )
        
        # The workflow should raise an exception due to non-serializable data
        with pytest.raises(Exception):
            await workflow.run()
    
    @pytest.mark.asyncio
    async def test_complex_nested_structures(self):
        """Test handling of complex nested data structures"""
        class ComplexDataNode(Node):
            def prepare(self, shared, request_input):
                return None
                
            def execute(self, prepared_result):
                return {
                    "level1": {
                        "level2": {
                            "level3": [1, 2, {"key": "value", "list": [True, False, None]}]
                        },
                        "another_key": [{"nested": True}, {"nested": False}]
                    },
                    "top_level": "value"
                }
                
            def cleanup(self, shared, prepared_result, execution_result):
                shared['complex_data'] = execution_result
                return execution_result
        
        complex_node = ComplexDataNode(id="complex")
        
        workflow = WorkflowEngine(
            nodes=[complex_node],
            start=complex_node
        )
        
        # Run the workflow - this should succeed as the data is JSON serializable
        continuing, tracking_data = await workflow.run()
        
        # Verify the complex data structure was preserved
        assert not continuing
        complex_data = tracking_data['steps'][-1]['shared']['complex_data']
        assert complex_data['top_level'] == "value"
        assert complex_data['level1']['level2']['level3'][2]['key'] == "value"
        assert complex_data['level1']['another_key'][0]['nested'] == True