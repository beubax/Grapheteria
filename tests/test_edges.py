import pytest
from grapheteria import Node, ExecutionState, WorkflowStatus

class SimpleNode(Node):
    """A simple test node implementation"""
    def prepare(self, shared, request_input):
        return shared
        
    def execute(self, prepared_result):
        # Just pass through data
        return prepared_result

@pytest.fixture
def base_workflow():
    """Create a basic workflow with nodes for testing"""
    start = SimpleNode(id="start")
    process_a = SimpleNode(id="process_a")
    process_b = SimpleNode(id="process_b")
    process_c = SimpleNode(id="process_c")
    end = SimpleNode(id="end")
    
    return {
        "start": start,
        "process_a": process_a,
        "process_b": process_b,
        "process_c": process_c,
        "end": end
    }

def test_basic_edge_connection(base_workflow):
    """Test basic edge connection without conditions"""
    start = base_workflow["start"]
    end = base_workflow["end"]
    
    # Connect nodes with a basic edge
    start > end
    
    # Create a state to test with
    state = ExecutionState(
        shared={},
        next_node_id="start",
        workflow_status=WorkflowStatus.HEALTHY
    )
    
    # Verify next node is correctly determined
    next_id = start.get_next_node_id(state)
    assert next_id == "end"

def test_edge_condition_evaluation(base_workflow):
    """Test that edge conditions evaluate correctly"""
    start = base_workflow["start"]
    process_a = base_workflow["process_a"]
    process_b = base_workflow["process_b"]
    
    # Add conditional edges
    start - "shared['route'] == 'A'" > process_a
    start - "shared['route'] == 'B'" > process_b
    
    # Test route A
    state_a = ExecutionState(
        shared={"route": "A"},
        next_node_id="start",
        workflow_status=WorkflowStatus.HEALTHY
    )
    
    next_id = start.get_next_node_id(state_a)
    assert next_id == "process_a"
    
    # Test route B
    state_b = ExecutionState(
        shared={"route": "B"},
        next_node_id="start",
        workflow_status=WorkflowStatus.HEALTHY
    )
    
    next_id = start.get_next_node_id(state_b)
    assert next_id == "process_b"

def test_true_condition_priority(base_workflow):
    """Test that 'True' condition always takes priority"""
    start = base_workflow["start"]
    process_a = base_workflow["process_a"]
    process_b = base_workflow["process_b"]
    process_c = base_workflow["process_c"]
    
    # Add edges with mixed conditions
    start - "shared['important'] == True" > process_a
    start - "True" > process_b
    start - "shared['route'] == 'C'" > process_c
    
    # Even with matching conditions, True should win
    state = ExecutionState(
        shared={"important": True, "route": "C"},
        next_node_id="start",
        workflow_status=WorkflowStatus.HEALTHY
    )
    
    next_id = start.get_next_node_id(state)
    assert next_id == "process_b"  # The "True" condition edge

def test_default_edge_fallback(base_workflow):
    """Test that default edge is used when no conditions match"""
    start = base_workflow["start"]
    process_a = base_workflow["process_a"]
    process_b = base_workflow["process_b"]
    end = base_workflow["end"]
    
    # Add conditional edges and a default
    start - "shared['route'] == 'A'" > process_a
    start - "shared['route'] == 'B'" > process_b
    start > end  # Default edge
    
    # No conditions match
    state = ExecutionState(
        shared={"route": "unknown"},
        next_node_id="start",
        workflow_status=WorkflowStatus.HEALTHY
    )
    
    next_id = start.get_next_node_id(state)
    assert next_id == "end"  # Should take the default edge

def test_first_matching_condition_wins(base_workflow):
    """Test that the first matching condition gets selected"""
    start = base_workflow["start"]
    process_a = base_workflow["process_a"]
    process_b = base_workflow["process_b"]
    
    # Add multiple matching conditions
    start - "shared['value'] > 50" > process_a
    start - "shared['value'] > 25" > process_b
    
    # Both conditions match, but first should win
    state = ExecutionState(
        shared={"value": 75},
        next_node_id="start",
        workflow_status=WorkflowStatus.HEALTHY
    )
    
    next_id = start.get_next_node_id(state)
    assert next_id == "process_a"  # First matching condition

def test_complex_condition(base_workflow):
    """Test complex conditions with multiple operators and checks"""
    start = base_workflow["start"]
    process_a = base_workflow["process_a"]
    process_b = base_workflow["process_b"]
    process_c = base_workflow["process_c"]
    
    # Add complex conditions
    start - "shared['score'] > 80 and shared['status'] == 'active'" > process_a
    start - "shared['score'] > 50 and shared['category'] in ['premium', 'vip']" > process_b
    start - "len(shared.get('history', [])) > 3" > process_c
    
    # Test complex condition matching
    state = ExecutionState(
        shared={
            "score": 90,
            "status": "active",
            "category": "standard",
            "history": [1, 2, 3, 4]
        },
        next_node_id="start",
        workflow_status=WorkflowStatus.HEALTHY
    )
    
    next_id = start.get_next_node_id(state)
    assert next_id == "process_a"  # First complex condition
    
    # Test another complex match
    state.shared["status"] = "inactive"
    state.shared["category"] = "premium"
    
    next_id = start.get_next_node_id(state)
    assert next_id == "process_b"  # Second complex condition
    
    # Test third complex match
    state.shared["score"] = 30
    state.shared["category"] = "standard"
    
    next_id = start.get_next_node_id(state)
    assert next_id == "process_c"  # Third complex condition

def test_edge_cases(base_workflow):
    """Test edge cases for edge condition evaluation"""
    start = base_workflow["start"]
    process_a = base_workflow["process_a"]
    process_b = base_workflow["process_b"]
    end = base_workflow["end"]
    
    # Test case 1: Empty shared state
    start - "shared.get('key', False)" > process_a
    start > end  # Default edge
    
    state = ExecutionState(
        shared={},
        next_node_id="start",
        workflow_status=WorkflowStatus.HEALTHY
    )
    
    next_id = start.get_next_node_id(state)
    assert next_id == "end"  # Default should be taken with empty shared
    
    # Clear edges and add new ones for next test
    start.edges.clear()
    
    # Test case 2: Invalid condition (syntax error) should be treated as False
    start - "this is not valid python" > process_a
    start > process_b  # Default
    
    next_id = start.get_next_node_id(state)
    assert next_id == "process_b"  # Default when condition has syntax error
    
    # Clear edges and add new ones for next test
    start.edges.clear()
    
    # Test case 3: No edges
    next_id = start.get_next_node_id(state)
    assert next_id is None  # No edges should return None
    
    # Test case 4: Only one unconditional edge
    start > process_a
    
    next_id = start.get_next_node_id(state)
    assert next_id == "process_a"

@pytest.mark.asyncio
async def test_edge_in_workflow_execution(base_workflow):
    """Test edges in actual workflow execution"""
    # Create nodes that modify shared state
    class IncrementingNode(Node):
        def prepare(self, shared, request_input):
            # Explicitly return the shared dictionary
            return shared
            
        def execute(self, prepared_result):
            # Now we know prepared_result is the shared dictionary
            prepared_result["count"] = prepared_result.get("count", 0) + 1
            return prepared_result
            
    class RoutingNode(Node):
        def prepare(self, shared, request_input):
            # Explicitly return the shared dictionary
            return shared
            
        def execute(self, prepared_result):
            # Set routing based on count
            if prepared_result.get("count", 0) > 2:
                prepared_result["route"] = "high"
            else:
                prepared_result["route"] = "low"
            return prepared_result
    
    # Create test workflow
    start = IncrementingNode(id="start")
    router = RoutingNode(id="router")
    high_path = IncrementingNode(id="high")
    low_path = IncrementingNode(id="low")
    end = IncrementingNode(id="end")
    
    # Connect with conditions
    start > router
    router - "shared['route'] == 'high'" > high_path
    router - "shared['route'] == 'low'" > low_path
    high_path > end
    low_path > end
    
    # Setup test execution state
    state = ExecutionState(
        shared={"count": 0},
        next_node_id="start",
        workflow_status=WorkflowStatus.HEALTHY
    )
    
    # Helper function to execute a node and get next
    async def execute_node(node_id):
        node = [n for n in [start, router, high_path, low_path, end] if n.id == node_id][0]
        prep_result = node.prepare(state.shared, lambda *args: None)
        exec_result = node.execute(prep_result)
        node.cleanup(state.shared, prep_result, exec_result)
        return node.get_next_node_id(state)
    
    # Run workflow
    current = "start"
    path = [current]
    
    while current:
        current = await execute_node(current)
        if current:
            path.append(current)
    
    # First run should go: start -> router -> low -> end
    assert path == ["start", "router", "low", "end"]
    assert state.shared["count"] == 3  # Incremented three times
    
    # Run again with higher initial count
    state.shared = {"count": 2}
    current = "start"
    path = [current]
    
    while current:
        current = await execute_node(current)
        if current:
            path.append(current)
    
    # Second run should go: start -> router -> high -> end
    assert path == ["start", "router", "high", "end"]
    assert state.shared["count"] == 5  # 2 + 3 more increments
