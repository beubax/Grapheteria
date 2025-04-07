import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

from grapheteria import Node, NodeStatus, ExecutionState

# ======= Test Fixtures =======

@pytest.fixture
def shared_state():
    """Sample shared state for testing."""
    return {
        "user_name": "Test User",
        "data": {"key1": "value1", "key2": 42}
    }

@pytest.fixture
def request_input_mock():
    """Mock for request_input function."""
    return AsyncMock(return_value="User input response")

@pytest.fixture
def execution_state():
    """Sample execution state for testing."""
    return ExecutionState(
        shared={"user_name": "Test User"},
        next_node_id="test_node",
        workflow_status="HEALTHY",
        node_statuses={}
    )

# ======= Basic Node Tests =======

class BasicNode(Node):
    """Simple node implementing all three phases."""
    def prepare(self, shared, request_input):
        return {"name": shared.get("user_name", "Unknown"), "counter": 0}
    
    def execute(self, prepared_result):
        return {"greeting": f"Hello, {prepared_result['name']}!", "counter": prepared_result["counter"] + 1}
    
    def cleanup(self, shared, prepared_result, execution_result):
        shared["greeting"] = execution_result["greeting"]
        shared["counter"] = execution_result["counter"]
        return execution_result


class TestBasicNodeExecution:
    async def test_prepare_phase(self, shared_state, request_input_mock):
        node = BasicNode()
        result = node.prepare(shared_state, request_input_mock)
        
        assert result == {"name": "Test User", "counter": 0}
        assert request_input_mock.call_count == 0  # Ensure it wasn't called
    
    async def test_execute_phase(self):
        node = BasicNode()
        prepared_data = {"name": "Test User", "counter": 0}
        
        result = node.execute(prepared_data)
        
        assert result["greeting"] == "Hello, Test User!"
        assert result["counter"] == 1
    
    async def test_cleanup_phase(self, shared_state):
        node = BasicNode()
        prepared_data = {"name": "Test User", "counter": 0}
        execution_result = {"greeting": "Hello, Test User!", "counter": 1}
        
        result = node.cleanup(shared_state, prepared_data, execution_result)
        
        assert result == execution_result
        assert shared_state["greeting"] == "Hello, Test User!"
        assert shared_state["counter"] == 1
    
    async def test_full_node_run(self, execution_state, request_input_mock):
        node = BasicNode(id="test_node")
        
        await node.run(execution_state, request_input_mock)
        
        assert execution_state.node_statuses["test_node"] == NodeStatus.COMPLETED
        assert execution_state.shared["greeting"] == "Hello, Test User!"
        assert execution_state.shared["counter"] == 1


# ======= Node Configuration Tests =======

class ConfigurableNode(Node):
    def prepare(self, shared, request_input):
        return {
            "greeting_template": self.config.get("greeting_template", "Hello, {name}!"),
            "name": shared.get("user_name", "Unknown")
        }
    
    def execute(self, prepared_result):
        return prepared_result["greeting_template"].format(name=prepared_result["name"])


class TestNodeConfiguration:
    async def test_default_config(self, shared_state, request_input_mock):
        node = ConfigurableNode()
        prepared = node.prepare(shared_state, request_input_mock)
        result = node.execute(prepared)
        
        assert result == "Hello, Test User!"
    
    async def test_custom_config(self, shared_state, request_input_mock):
        node = ConfigurableNode(config={"greeting_template": "Greetings, {name}! How are you today?"})
        prepared = node.prepare(shared_state, request_input_mock)
        result = node.execute(prepared)
        
        assert result == "Greetings, Test User! How are you today?"
    
    async def test_reusable_node_different_configs(self, shared_state, request_input_mock):
        formal_node = ConfigurableNode(config={"greeting_template": "Dear {name},"})
        casual_node = ConfigurableNode(config={"greeting_template": "Hey {name}!"})
        
        formal_prepared = formal_node.prepare(shared_state, request_input_mock)
        casual_prepared = casual_node.prepare(shared_state, request_input_mock)
        
        formal_result = formal_node.execute(formal_prepared)
        casual_result = casual_node.execute(casual_prepared)
        
        assert formal_result == "Dear Test User,"
        assert casual_result == "Hey Test User!"


# ======= Retry and Fallback Tests =======

class FlakyNode(Node):
    def __init__(self, id=None, config=None, fail_times=2):
        super().__init__(id, config, max_retries=3, wait=0.01)
        self.attempts = 0
        self.fail_times = fail_times
    
    def execute(self, prepared_result):
        self.attempts += 1
        if self.attempts <= self.fail_times:
            raise ValueError(f"Simulated failure on attempt {self.attempts}")
        return f"Success on attempt {self.attempts}"
    
    def exec_fallback(self, prepared_result, exception):
        return f"Fallback activated after {self.attempts} attempts: {str(exception)}"


class TestRetryAndFallback:
    async def test_successful_retry(self):
        node = FlakyNode(fail_times=2)  # Will succeed on third try
        result = await node._execute_with_retry(None)
        
        assert result == "Success on attempt 3"
        assert node.attempts == 3
    
    async def test_fallback_after_all_retries(self):
        node = FlakyNode(fail_times=5)  # Will never succeed within retry limit
        result = await node._execute_with_retry(None)
        
        assert "Fallback activated after" in result
        assert node.attempts == node.max_retries
    
    async def test_no_retries_needed(self):
        node = FlakyNode(fail_times=0)  # Will succeed on first try
        result = await node._execute_with_retry(None)
        
        assert result == "Success on attempt 1"
        assert node.attempts == 1


# ======= Async Node Tests =======

class AsyncNode(Node):
    async def prepare(self, shared, request_input):
        # Simulate async database lookup
        await asyncio.sleep(0.01)
        return {"user_id": shared.get("user_id", 0)}
    
    async def execute(self, prepared_result):
        # Simulate async API call
        await asyncio.sleep(0.01)
        return {"api_result": f"Data for user {prepared_result['user_id']}"}
    
    async def cleanup(self, shared, prepared_result, execution_result):
        # Simulate async cache update
        await asyncio.sleep(0.01)
        shared["api_cache"] = execution_result["api_result"]
        return execution_result


class TestAsyncNode:
    async def test_async_prepare(self, request_input_mock):
        node = AsyncNode()
        shared = {"user_id": 42}
        
        result = await node.prepare(shared, request_input_mock)
        
        assert result == {"user_id": 42}
    
    async def test_async_execute(self):
        node = AsyncNode()
        prepared = {"user_id": 42}
        
        result = await node.execute(prepared)
        
        assert result == {"api_result": "Data for user 42"}
    
    async def test_async_cleanup(self):
        node = AsyncNode()
        shared = {}
        prepared = {"user_id": 42}
        execution_result = {"api_result": "Data for user 42"}
        
        result = await node.cleanup(shared, prepared, execution_result)
        
        assert result == execution_result
        assert shared["api_cache"] == "Data for user 42"
    
    async def test_full_async_node_run(self, execution_state, request_input_mock):
        execution_state.shared["user_id"] = 42
        node = AsyncNode(id="test_node")
        
        await node.run(execution_state, request_input_mock)
        
        assert execution_state.node_statuses["test_node"] == NodeStatus.COMPLETED
        assert execution_state.shared["api_cache"] == "Data for user 42"


# ======= request_input Tests =======

class InputRequestNode(Node):
    async def prepare(self, shared, request_input):
        # Ask for user confirmation
        confirm = await request_input(
            prompt="Proceed with operation?",
            options=["Yes", "No"],
            input_type="select"
        )
        
        # Pass request_input to execute
        return {
            "confirmed": confirm == "Yes",
            "request_input": request_input
        }
    
    async def execute(self, prepared_result):
        if not prepared_result["confirmed"]:
            # Get reason using a different request_id
            reason = await prepared_result["request_input"](
                prompt="Why not?",
                input_type="text",
                request_id="rejection_reason"
            )
            return {"status": "rejected", "reason": reason}
        
        return {"status": "approved"}


@pytest.mark.parametrize("user_inputs,expected_result", [
    ({"test_node": "Yes"}, {"status": "approved"}),
    ({"test_node": "No", "rejection_reason": "Too expensive"}, {"status": "rejected", "reason": "Too expensive"})
])
class TestRequestInput:
    async def test_input_requests(self, execution_state, user_inputs, expected_result):
        node = InputRequestNode(id="test_node")
        
        # Create custom request_input that returns values from user_inputs
        async def custom_request_input(prompt=None, options=None, input_type=None, request_id=None):
            actual_id = request_id or "test_node"
            if actual_id not in user_inputs:
                return "Default response"
            return user_inputs[actual_id]
        
        # Run the node
        await node.run(execution_state, custom_request_input)
        
        # Check if node was completed
        assert execution_state.node_statuses["test_node"] == NodeStatus.COMPLETED


# ======= Standalone Node Tests =======

class StandaloneNode(Node):
    def prepare(self, shared, request_input):
        return {"data": shared.get("input_data", "default")}
    
    def execute(self, prepared_result):
        return prepared_result["data"].upper()
    
    def cleanup(self, shared, prepared_result, execution_result):
        shared["result"] = execution_result
        return execution_result


class TestStandaloneNode:
    async def test_run_standalone(self):
        node = StandaloneNode()
        initial_state = {"input_data": "test string"}
        
        result = await node.run_standalone(initial_state)
        
        assert result["result"] == "TEST STRING"
    
    async def test_run_standalone_empty_state(self):
        node = StandaloneNode()
        
        result = await node.run_standalone({})
        
        assert result["result"] == "DEFAULT"
    
    @pytest.mark.xfail(raises=NotImplementedError)
    async def test_request_input_not_available_in_standalone(self):
        class BadStandaloneNode(Node):
            def prepare(self, shared, request_input):
                # This will fail in standalone mode
                return request_input("This shouldn't work")
        
        node = BadStandaloneNode()
        await node.run_standalone({})


# ======= Edge Cases =======

class TestEdgeCases:
    async def test_empty_node(self, execution_state, request_input_mock):
        """Test a node that doesn't override any methods."""
        class EmptyNode(Node):
            pass
        
        node = EmptyNode(id="empty_node")
        await node.run(execution_state, request_input_mock)
        
        assert execution_state.node_statuses["empty_node"] == NodeStatus.COMPLETED
    
    async def test_exception_handling(self, execution_state, request_input_mock):
        """Test that exceptions in node execution are properly handled."""
        class ExplodingNode(Node):
            def execute(self, prepared_result):
                raise ValueError("Boom!")
        
        node = ExplodingNode(id="exploding_node")
        
        with pytest.raises(ValueError, match="Boom!"):
            await node.run(execution_state, request_input_mock)
        
        assert execution_state.node_statuses["exploding_node"] == NodeStatus.FAILED
        assert "error" in execution_state.metadata
        assert "ValueError: Boom!" in execution_state.metadata["error"]
    
    async def test_prepare_returns_none(self, execution_state, request_input_mock):
        """Test that a node works when prepare returns None."""
        class NonePreparationNode(Node):
            def prepare(self, shared, request_input):
                return None
            
            def execute(self, prepared_result):
                return "executed with None"
        
        node = NonePreparationNode(id="none_prep_node")
        await node.run(execution_state, request_input_mock)
        
        assert execution_state.node_statuses["none_prep_node"] == NodeStatus.COMPLETED