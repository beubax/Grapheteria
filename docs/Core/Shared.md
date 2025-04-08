# Using the Shared Dictionary

## Overview

The shared dictionary is your workflow's memory bank - the primary way nodes talk to each other. Think of it as a communal whiteboard where any node can read existing information or write new data. It's simply a Python dictionary accessible to all nodes in your workflow.

```python
def prepare(self, shared, request_input):
    # Read something from shared state
    previous_result = shared.get('previous_calculation', 0)
    
    # Use that data in calculations
    return previous_result * 2

def cleanup(self, shared, prepared_result, execution_result):
    # Write back to shared state for other nodes
    shared['my_calculation'] = execution_result
    return execution_result
```

## Setting Initial State

By default, the shared dictionary starts empty (`{}`), but you can pre-load it with initial values that will evolve during workflow execution:

```python
# When creating a workflow from code
workflow = WorkflowEngine(
    nodes=[node1, node2, node3],
    start_node=node1,
    initial_shared_state={
        "chat_history": [],
        "processing_results": [],
        "retry_count": 0,
        "last_execution_time": None
    }
)
```

Remember that the shared dictionary is meant for dynamic values that change as your workflow runs. For fixed inputs, use node configuration parameters instead.

Setting the same initial state in JSON which can be used with .... yeah yeah the UI, you get it.

```json
{
  "nodes": [...],
  "edges": [...],
  "initial_state": {
    "user_profile": {
      "name": "Alice",
      "preferences": ["quick", "automated"]
    }
  }
}
```

## Serialization Constraints

Since workflow states are saved to disk, variables in your shared dictionary must be JSON-serializable by default. This includes:

- Simple types: strings, numbers, booleans, None
- Containers: lists, dictionaries
- Nested combinations of the above

```python
# ✅ This works fine
shared["results"] = [1, 2, 3]
shared["config"] = {"max_retries": 3, "enabled": True}

# ❌ This will cause errors during state saving
shared["queue"] = queue.Queue()  # Not JSON serializable
shared["model"] = sklearn.linear_model.LinearRegression()  # Not serializable
```

Need to store complex Python objects? You'll need to extend the storage backend to use pickle or another serialization method. See our [Extending Storage](extending-storage.md) guide for the full details.