---
layout: default
title: "Node"
parent: "Core"
nav_order: 1
---

# Working with Nodes in Grapheteria

## Overview

The Node class is the smallest unit of execution in Grapheteria's workflow system - think of it as the atom in your workflow molecule. All task-performing classes must extend this class to join the workflow party. Nodes handle individual pieces of work, process data, make decisions, or interact with external systems.

```python
from grapheteria import Node

class MyCustomNode(Node):
    async def execute(self, prepared_result):
        # Your execution logic goes here
        return "Hello, Grapheteria!"
```

## The Triple-Phase Execution Model

Grapheteria nodes follow a clear three-phase execution model inspired by PocketFlow, bringing order to the potentially chaotic world of workflow execution. This separation creates clear boundaries for different responsibilities and improves maintainability.

### 1. Prepare

The prepare phase sets the stage for execution. It receives two parameters:
- `shared`: The shared state dictionary for cross-node communication
- `request_input`: A function that can request input during execution

```python
def prepare(self, shared, request_input):
    # Extract what you need from shared state
    name = shared.get("user_name", "friend")
    initial_data = shared.get("data", {})
    # Return exactly what execute needs - nothing more, nothing less
    return {"name": name, "greeting": "Hello", "data": initial_data}
```

### 2. Execute

The execute phase is where the magic happens. While it used to be required, you can now customize any of the three phases as needed. It receives one parameter:
- `prepared_result`: The output from the prepare phase

```python
def execute(self, prepared_result):
    # The main work happens here, using only what prepare provided
    processed_data = do_something_with(prepared_result["data"])
    return {
        "message": f"{prepared_result['greeting']}, {prepared_result['name']}!",
        "processed_data": processed_data
    }
```

Notice how `execute` doesn't receive the shared state directly. This is intentional! It:
1. Prevents accidental corruption of shared state during critical operations
2. Enables future parallel execution of multiple nodes ([see Parallelism docs](parallelism.md))
3. Forces clean separation of concerns between phases

Execution comes with built-in resilience:
- `max_retries`: Number of attempts before giving up (default: 1)
- `wait`: Time to wait between retries in seconds
- `exec_fallback`: Method called when all retries fail

```python
class ReliableNode(Node):
    def execute(self, prepared_result):
        # Potentially flaky operation
        return call_external_api()
        
    def exec_fallback(self, prepared_result, exception):
        # Handle the failure gracefully
        return {"status": "failed", "reason": str(exception)}

# Create instance with retry parameters
reliable_api = ReliableNode(config={"api_key": "xyz123"}, max_retries=3, wait=2)
```

Here's an example using async/await with an LLM API:

```python
class LLMNode(Node):
    async def execute(self, prepared_result):
        prompt = prepared_result["prompt"]
        system_message = prepared_result["system_message"]
        
        # Simply await an external API call
        response = await self.call_llm_api(system_message, prompt)
        
        return {
            "response": response.text,
            "tokens_used": response.total_tokens
        }
```

### 3. Cleanup

The cleanup phase handles post-execution tasks. It receives all three pieces of context:
- `shared`: The shared state dictionary
- `prepared_result`: The original output from prepare
- `execution_result`: The output from execute

```python
def cleanup(self, shared, prepared_result, execution_result):
    # Update shared state with our results
    shared["greeting_message"] = execution_result["message"]
    shared["processed_data"] = execution_result["processed_data"]
    # Optionally return something if another node connects directly
    return execution_result
```

## Custom Node IDs

Always define a custom ID for each node rather than relying on auto-generated IDs:

```python
# Good: Descriptive, unique ID
node = MyCustomNode(id="validate_user_input_step")

# Bad: Relying on auto-generated ID
node = MyCustomNode()  # Gets something like "MyCustomNode_a1b2c3d4"
```

Custom IDs are crucial for:
1. Logging and debugging - imagine searching logs for "validate_user_input_step" vs "MyCustomNode_a1b2c3d4"
2. Resuming workflows after interruption - when restarting a workflow, the system needs to know exactly which node to resume from
3. Providing data to halted nodes requesting human input - when a node is waiting for input, you need a clear ID to send that input to the right place

Without meaningful IDs, your workflow becomes a mysterious black box. With them, it transforms into a transparent, manageable, and resumable process.

## Node Configuration

Nodes can be configured through a config dictionary passed during initialization. This enhances reusability - the same node class can be used for multiple purposes just by changing its configuration.

```python
# Create two different LLM agents from the same class
customer_service = LLMNode(id = "customer_service", config={
    "system_prompt": "You are a helpful customer service representative.",
    "temperature": 0.3,
    "max_tokens": 500
})

creative_writer = LLMNode(id="creative_writer", config={
    "system_prompt": "You are a creative storyteller with a flair for drama.",
    "temperature": 0.9,
    "max_tokens": 2000
})
```

Access config values inside your node methods:

```python
def prepare(self, shared, request_input):
    system_prompt = self.config.get("system_prompt", "Default system prompt")
    temperature = self.config.get("temperature", 0.7)
    return {
        "system_message": system_prompt,
        "prompt": shared.get("user_message", ""),
        "temperature": temperature
    }
```

## Using request_input

The `request_input` function allows nodes to request external input during execution - perfect for human-in-the-loop scenarios. The function can be called without any parameters, though additional information helps guide the user:

```python
async def prepare(self, shared, request_input):
    # Simple confirmation prompt - with helpful parameters
    user_choice = await request_input(
        prompt="Do you approve this transaction?",
        options=["Approve", "Reject"],
        input_type="select"
    )
    
    # If rejection, ask for reason in the same prepare phase
    if user_choice == "Reject":
        reason = await request_input(
            prompt="Please provide reason for rejection:",
            input_type="text",
            request_id="rejection_reason"  # Different from default node ID
        )
        return {"status": "rejected", "reason": reason}
    
    # Store the choice for execute phase
    return {"user_approved": True}
```

The `request_id` parameter differentiates between multiple input requests within the same node. Without it, the same input would be reused for all calls (defaulting to the node's ID).

## Running Nodes Standalone

For testing and debugging, you can run nodes independently without setting up an entire workflow:

```python
import asyncio

async def test_node():
    # Create initial shared state
    shared_state = {"user_name": "Grapheteria Fan", "data": {"key": "value"}}
    
    # Create and run the node
    node = ProcessingNode(config={"processing_level": "detailed"})
    result = await node.run_standalone(shared_state)
    
    print(f"Updated shared state: {result}")
    print(f"Processed data: {result.get('processed_data')}")

# Run it
asyncio.run(test_node())
```

Note that `request_input` functionality won't work in standalone mode - it's strictly for testing node logic without human interaction.

## Initializing Nodes in JSON and Code

Grapheteria offers flexibility by letting you define workflows in both Python code and JSON. While your Node class implementation must be in Python, you can instantiate and connect nodes using either approach.

### In Code (Python)

```python
# Create a processing node with a custom ID and configuration
processor = MyCustomNode(
    id="data_processor_1", 
    config={"max_items": 100, "verbose": True}
)
```

### In JSON

```json
{
  "nodes": [
    {
      "id": "data_processor_1",
      "class": "MyCustomNode",
      "config": {
        "max_items": 100,
        "verbose": true
      }
    }
  ]
}
```

> **Why JSON?** JSON workflows sync in real-time with the UI, letting programmers design and modify workflows visually with an intuitive debugging experience, while automatically generating the underlying configuration. It also makes workflows portable, versionable, and easier to inspect. 


With these building blocks, you can create nodes that graph-itefully handle any workflow task your application needs!

