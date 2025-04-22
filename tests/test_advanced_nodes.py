import pytest
import asyncio
from grapheteria import Node, ExecutionState, WorkflowStatus, NodeStatus

# Helpers for testing
async def run_node_with_state(node, initial_state=None):
    state = ExecutionState(
        shared=initial_state or {},
        next_node_id=node.id,
        workflow_status=WorkflowStatus.HEALTHY,
        node_statuses={}
    )
    
    async def mock_request_input(*args, **kwargs):
        return "mock input"
    
    await node.run(state, mock_request_input)
    return state

# Test Async Node
class TestAsyncNode:
    class AsyncTestNode(Node):
        async def prepare(self, shared, request_input):
            shared["prepare_ran"] = True
            return "prepared data"
        
        async def execute(self, prepared_data):
            await asyncio.sleep(0.1)  # Simulate async work
            return f"executed: {prepared_data}"
        
        async def cleanup(self, shared, prepared_data, execution_result):
            shared["cleanup_ran"] = True
            shared["result"] = execution_result
    
    @pytest.mark.asyncio
    async def test_async_methods(self):
        node = self.AsyncTestNode()
        state = await run_node_with_state(node)
        
        assert state.shared["prepare_ran"] is True
        assert state.shared["cleanup_ran"] is True
        assert state.shared["result"] == "executed: prepared data"
        assert state.node_statuses[node.id] == NodeStatus.COMPLETED

# Test Parallel Node
class TestParallelNode:
    class ParallelTestNode(Node):
        async def prepare(self, shared, request_input):
            if "items" in shared:
                return shared["items"]
            return [{"id": i} for i in range(shared.get("item_count", 3))]
        
        async def _execute_with_retry(self, items):
            tasks = [self._process_item(item) for item in items]
            results = await asyncio.gather(*tasks, return_exceptions=True)
            exceptions = [r for r in results if isinstance(r, Exception)]
            if exceptions:
                raise exceptions[0]
                
            return results
        
        async def execute(self, item):
            await asyncio.sleep(0.05)  # Simulate some work
            print("Item", item)
            if item.get("id") == 99:  # Simulate failure case
                raise ValueError("Item 99 always fails")
            return f"processed-{item['id']}"
        
        def cleanup(self, shared, prepared_data, execution_result):
            if "parallel_results" not in shared:
                shared["parallel_results"] = []
            shared["parallel_results"].extend(execution_result)
    
    @pytest.mark.asyncio
    async def test_parallel_processing(self):
        node = self.ParallelTestNode()
        state = await run_node_with_state(node, {"item_count": 5})
        
        assert len(state.shared["parallel_results"]) == 5
        assert state.shared["parallel_results"] == [
            "processed-0", "processed-1", "processed-2", "processed-3", "processed-4"
        ]
    
    @pytest.mark.asyncio
    async def test_empty_item_list(self):
        node = self.ParallelTestNode()
        state = await run_node_with_state(node, {"item_count": 0})
        
        assert "parallel_results" in state.shared
        assert state.shared["parallel_results"] == []
    
    @pytest.mark.asyncio
    async def test_failure_propagation(self):
        node = self.ParallelTestNode()
        
        with pytest.raises(ValueError, match="Item 99 always fails"):
            await run_node_with_state(node, {"item_count": 3, "items": [{"id": 1}, {"id": 99}, {"id": 3}]})

# Test Batch Node
class TestBatchNode:
    class BatchTestNode(Node):
        def prepare(self, shared, request_input):
            return [f"item-{i}" for i in range(shared.get("batch_size", 3))]
        
        async def _execute_with_retry(self, items):
            results = []
            for item in items:
                for self.cur_retry in range(self.max_retries):
                    try:
                        result = await super()._process_item(item)  
                        break
                    except Exception as e:
                        if self.cur_retry == self.max_retries - 1:
                            return await self._handle_fallback(item, e)
                        if self.wait > 0:
                            await asyncio.sleep(self.wait)
                results.append(result)
            return results
        
        def execute(self, item):
            if item == "item-fail":
                raise ValueError("Failed item")
            return f"processed-{item}"
        
        def cleanup(self, shared, prepared_data, execution_result):
            if "batch_results" not in shared:
                shared["batch_results"] = []
            shared["batch_results"].extend(execution_result)
    
    @pytest.mark.asyncio
    async def test_batch_processing(self):
        node = self.BatchTestNode()
        state = await run_node_with_state(node, {"batch_size": 4})
        
        assert len(state.shared["batch_results"]) == 4
        assert state.shared["batch_results"] == [
            "processed-item-0", "processed-item-1", "processed-item-2", "processed-item-3"
        ]
    
    @pytest.mark.asyncio
    async def test_empty_batch(self):
        node = self.BatchTestNode()
        state = await run_node_with_state(node, {"batch_size": 0})
        
        assert "batch_results" in state.shared
        assert state.shared["batch_results"] == []
    
    @pytest.mark.asyncio
    async def test_batch_with_retries(self):
        class RetryBatchNode(self.BatchTestNode):
            def __init__(self):
                super().__init__(max_retries=3, wait=0.01)
                self.attempt_counts = {}

            def prepare(self, shared, request_input):
                return shared.get("test_items")
            
            def execute(self, item):
                if item not in self.attempt_counts:
                    self.attempt_counts[item] = 0
                self.attempt_counts[item] += 1
                
                # Succeed on the second try for this item
                if item == "item-retry" and self.attempt_counts[item] < 2:
                    raise ValueError("Temporary failure")
                
            
                
                return f"processed-{item}-attempt-{self.attempt_counts[item]}"
        
        node = RetryBatchNode()
        _ = await run_node_with_state(node, {"batch_size": 2, "test_items": ["item-normal", "item-retry"]})
        
        # Second item should have required 2 attempts
        assert node.attempt_counts["item-normal"] == 1
        assert node.attempt_counts["item-retry"] == 2

# Test Error Handling with Fallback
class TestErrorHandling:
    class FallbackTestNode(Node):
        def __init__(self):
            super().__init__(max_retries=2)
            self.retries = 0
        
        def prepare(self, shared, request_input):
            return shared.get("test_data", 0)
        
        def execute(self, item):
            if item == 0:
                raise ZeroDivisionError("Cannot divide by zero")
            return 10 / item
        
        def exec_fallback(self, prepared_result, exception):
            return {"error": str(exception), "fallback_value": float('inf')}
        
        def cleanup(self, shared, prepared_result, execution_result):
            shared["result"] = execution_result
    
    @pytest.mark.asyncio
    async def test_fallback_execution(self):
        node = self.FallbackTestNode()
        
        # Test successful case
        state = await run_node_with_state(node, {"test_data": 2})
        assert state.node_statuses[node.id] == NodeStatus.COMPLETED
        
        # Test fallback case
        state = await run_node_with_state(node, {"test_data": 0})
        assert state.node_statuses[node.id] == NodeStatus.COMPLETED
        assert "error" in state.shared["result"]
        assert state.shared["result"]["fallback_value"] == float('inf')
    
    class ParallelWithFallbackNode(Node):
        async def prepare(self, shared, request_input):
            return shared.get("items", [1, 2, 0, 4])
        
        async def _execute_with_retry(self, items):
            try:
                tasks = [self._process_item(item) for item in items]
                results = await asyncio.gather(*tasks, return_exceptions=True)
                
                # Check if any exceptions
                exceptions = [r for r in results if isinstance(r, Exception)]
                if exceptions:
                    raise exceptions[0]
                    
                return results
            except Exception as e:
                return await self._handle_fallback(items, e)
        
        async def execute(self, item):
            if item == 0:
                raise ZeroDivisionError("Cannot divide by zero")
            return 10 / item
        
        def exec_fallback(self, prepared_result, exception):
            return {
                "error": str(exception),
                "fallback_values": [
                    (10 / item if item != 0 else float('inf')) 
                    for item in prepared_result
                ]
            }
        
        def cleanup(self, shared, prepared_result, execution_result):
            shared["result"] = execution_result
    
    @pytest.mark.asyncio
    async def test_parallel_fallback(self):
        node = self.ParallelWithFallbackNode()
        state = await run_node_with_state(node)
        
        assert "error" in state.shared["result"]
        assert len(state.shared["result"]["fallback_values"]) == 4
        assert state.shared["result"]["fallback_values"][2] == float('inf')  # The zero case