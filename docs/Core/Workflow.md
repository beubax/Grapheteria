---
layout: default
title: "Workflow Engine"
parent: "Core"
nav_order: 4
---

# Grapheteria Workflow Engine Documentation

## Bringing It All Together: The WorkflowEngine

Now that we've defined our nodes, edges, and shared variables, it's time to fire up the engine! The `WorkflowEngine` class is where all the magic happens - it's the conductor that orchestrates your workflow from start to finish.

```python
from grapheteria import WorkflowEngine, Node1, Node2, Node3

# Create nodes and connect them
start_node = Node1(id="start")
middle_node = Node2(id="process")
end_node = Node3(id="finish")

start_node > middle_node > end_node

# Initialize the engine with our nodes
engine = WorkflowEngine(
    nodes=[start_node, middle_node, end_node],
    start=start_node,
    initial_shared_state={"counter": 0}
)
```

## JSON or Code? Choose Your Adventure

The workflow engine is flexible - you can define workflows either through code (as shown above) or via JSON files.

### Code-Based Workflows

With code-based workflows, you directly pass your node objects as a list:

```python
# Create your node instances
node1 = TextProcessorNode(id="process_text")
node2 = DatabaseNode(id="save_results")
node3 = NotificationNode(id="notify_user")

# The workflow_id is optional - a random one will be generated if not provided
engine = WorkflowEngine(
    nodes=[node1, node2, node3],
    workflow_id="my_awesome_workflow"
)
```

### JSON-Based Workflows

You might have a JSON file with the following format - 

```json
# workflows/data_pipeline.json
{
  "nodes": [...],
  "edges": [...],
  "initial_state": {...}
}
```

For JSON workflows, you need to import all node classes first, then provide the path or ID:

```python
# IMPORTANT: Import all node classes used in your JSON workflow
from my_nodes import TextProcessorNode, DatabaseNode, NotificationNode
from more_nodes import ValidationNode, TransformationNode

# The imports register the nodes with Grapheteria's registry
# Now you can load the workflow without initializing any nodes yourself

# Using workflow_path
engine = WorkflowEngine(workflow_path="workflows/data_pipeline.json")

# Or using workflow_id (will look for workflows/data_pipeline.json)
engine = WorkflowEngine(workflow_id="workflows.data_pipeline")
```

This works because Grapheteria automatically registers node classes when they're imported. The engine then instantiates the right classes based on the JSON definition.
The conversion is simple: dots in IDs become slashes in paths, making workflows.data_pipeline equal to workflows/data_pipeline.json.

## Ready, Set, Start!

Every workflow needs a starting point. If you don't explicitly set one, the engine will default to the first node in your list.

```python
# Explicitly setting the start node (recommended)
engine = WorkflowEngine(
    nodes=[node1, node2, node3],
    start=node2  # We're starting with node2, not node1
)

# Without setting start - will use the first node in the list
engine = WorkflowEngine(nodes=[node1, node2, node3])  # Will start with node1
```

## Time Travel with Run IDs

Each time you create a workflow engine, a unique run ID is generated. This ID is your time machine ticket - save it, and you can resume your workflow later!

```python
# Start a new workflow
engine = WorkflowEngine(nodes=[node1, node2, node3])
print(f"Save this ID to resume later: {engine.run_id}")

# Run a few steps...
continuing, tracking_data = await engine.run()

# Later, resume from where you left off
resumed_engine = WorkflowEngine(
    workflow_id="my_workflow",
    run_id="20240615_123045_789"
)
```

## Monitoring Workflow State

The heart of the engine is the `execution_state`, which gives you real-time information about what's happening in your workflow:

```python
# Check the current status of your workflow
workflow_status = engine.execution_state.workflow_status
print(f"Current status: {workflow_status}")  # RUNNING, COMPLETED, WAITING_FOR_INPUT, etc.

# See what node is up next
next_node = engine.execution_state.next_node_id
print(f"Next node to execute: {next_node}")

# Inspect the shared variables
shared_data = engine.execution_state.shared
print(f"Current counter value: {shared_data['counter']}")
```

The engine also maintains a complete history in `tracking_data` (we'll cover this in more detail later), which captures the entire journey of your workflow for logging and analysis.

## "Human in the Loop": Responding to Input Requests

When your workflow needs human input, it'll pause and wait. You can easily check if input is needed:

```python
# Check if the workflow is waiting for user input
if engine.execution_state.workflow_status == WorkflowStatus.WAITING_FOR_INPUT:
    input_request = engine.execution_state.awaiting_input
    node_id = input_request['node_id']
    prompt = input_request['prompt']
    
    print(f"Workflow is asking: {prompt}")
    
    # Provide the requested input and continue
    user_response = input("> ")
    continuing, _ = await engine.step({node_id: user_response})
```

The input you provide is keyed by the node ID that requested it - this way, the engine knows exactly where to route your response.

## Running Your Workflow: Baby Steps or Full Speed

The engine gives you two ways to run your workflow:

### Take One Step at a Time

Perfect for debugging or when you need granular control:

```python
# Execute just one node and stop
continuing, _ = await engine.step()

# If user input was requested, provide it in the next step
if engine.execution_state.awaiting_input:
    node_id = engine.execution_state.awaiting_input['node_id']
    continuing, _ = await engine.step({node_id: "user response"})
```

### Full Speed Ahead

When you're ready to let it rip:

```python
# Run the entire workflow until completion or until input is required
continuing, _ = await engine.run()

# If continuing is True and input is awaited, provide input to continue
if continuing and engine.execution_state.awaiting_input:
    node_id = engine.execution_state.awaiting_input['node_id']
    continuing, _ = await engine.run({node_id: "user response"})
```

And there you have it! From defining individual nodes to orchestrating complex workflows, Grapheteria gives you the power to create state machines that are both powerful and maintainable. Happy flow-charting!
