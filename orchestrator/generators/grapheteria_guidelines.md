# Grapheteria Guidelines

Grapheteria is a framework for building state-machine-based workflows. It enables the creation of complex, multi-step processes with conditional branching, input handling, and error management.

## Core Components

### 1. Node

Base class for all workflow nodes. Each node should:
- Define `prepare`, `execute`, and `cleanup` methods
- Handle errors appropriately
- Communicate with the workflow state through the shared dictionary

Node methods:
```python
def prepare(self, shared, request_input):
    """Prepare data for execution, can request user input if needed."""
    # Access data from shared state
    # Return data to be passed to execute
    return prepared_data
    
def execute(self, prepared_data):
    """Execute node logic."""
    # Process the prepared data
    # Return results
    return execution_result
    
def cleanup(self, shared, prepared_data, execution_result):
    """Store results in shared state and clean up."""
    # Update shared state with results
    shared["some_key"] = execution_result
```

### 2. Edge

Connects nodes together, optionally with conditions for branching logic:
```python
# Simple edge
node_a > node_b

# Conditional edge
node_a - "shared['status'] == 'success'" > success_node
node_a - "shared['status'] == 'failure'" > failure_node
```

### 3. WorkflowEngine

Executes the workflow, handles state persistence, and manages execution flow.

## Creating Custom Nodes

1. Import the necessary components:
```python
from grapheteria import Node
```

2. Define your custom node class:
```python
class MyCustomNode(Node):
    def prepare(self, shared, request_input):
        # Access data from shared state
        input_data = shared.get("input_data", {})
        
        # Optionally request user input
        if "user_input" not in shared:
            user_input = await request_input(
                prompt="Please enter some data:",
                input_type="text"
            )
            shared["user_input"] = user_input
        
        return input_data
    
    def execute(self, prepared_data):
        # Process the data
        result = some_processing(prepared_data)
        return result
    
    def cleanup(self, shared, prepared_data, execution_result):
        # Store results in shared state
        shared["result"] = execution_result
```

## Request Input

The `request_input` function in `prepare` can be used to request input from the user:

```python
await request_input(
    prompt="Please enter a value:",  # Text prompt to display
    options=["option1", "option2"],  # Optional list of choices
    input_type="text",               # "text", "select", "multiselect", etc.
    request_id="unique_id"           # Optional unique ID for the request
)
```

## Error Handling

Nodes should handle errors appropriately:

```python
def execute(self, prepared_data):
    try:
        # Attempt to process data
        result = some_processing(prepared_data)
        return result
    except Exception as e:
        # Handle the error
        # You can either raise the error to fail the node
        # or return a fallback value
        return {"error": str(e), "fallback": True}
```

## JSON Schema Format

Workflows can be defined in JSON format:

```json
{
  "nodes": [
    {
      "id": "start_node",
      "class": "StartNode",
      "config": {
        "parameter1": "value1",
        "parameter2": "value2"
      }
    },
    {
      "id": "process_node",
      "class": "ProcessNode",
      "config": {}
    },
    {
      "id": "end_node",
      "class": "EndNode",
      "config": {}
    }
  ],
  "edges": [
    {
      "from": "start_node",
      "to": "process_node",
      "condition": ""
    },
    {
      "from": "process_node",
      "to": "end_node",
      "condition": "shared['status'] == 'success'"
    }
  ],
  "start": "start_node",
  "initial_state": {
    "parameter": "initial_value"
  }
}
```

## Examples of Common Node Types

1. **InputNode**: Collects user input
2. **ProcessingNode**: Performs calculations or data transformations
3. **APINode**: Makes API calls to external services
4. **DecisionNode**: Makes decisions based on data
5. **OutputNode**: Presents results to the user

## Best Practices

1. **Statelessness**: Nodes should be stateless, storing all state in the shared dictionary
2. **Error Handling**: Handle errors gracefully with fallback options when appropriate
3. **Modularity**: Design nodes to be reusable across different workflows
4. **Input Validation**: Validate inputs in the prepare method
5. **Documentation**: Document each node's purpose, inputs, and outputs 