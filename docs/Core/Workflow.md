---
layout: default
title: "Workflow Engine"
parent: "Core"
nav_order: 4
---

# Workflow Orchestration

## Bringing It All Together: The Workflow Engine

Now that we've defined our nodes, edges, and shared variables, it's time to fire up the engine! The `WorkflowEngine` class is where all the magic happens - it's the conductor that orchestrates your workflow from start to finish.

```python
from grapheteria import WorkflowEngine
from nodes import Node1, Node2, Node3

# Create nodes
start_node = Node1(id="start")
middle_node = Node2(id="process")
end_node = Node3(id="finish")

start_node > middle_node > end_node #Connect them

shared_initial = {"counter": 0} #Initialize the shared variable

# Initialize the engine with our nodes
engine = WorkflowEngine(
    nodes=[start_node, middle_node, end_node],
    start=start_node,
    initial_shared_state=shared_initial
)
```

## JSON or Code? Choose Your Adventure

The workflow engine is flexible - you can define your workflow schema either through code (as shown above) or via JSON files.

### Code-Based Schema

With code-based schema definitions, you directly pass your node objects as a list:

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

### JSON-Based Schema

You might have a JSON file with the following format -
```json
{
  "nodes": ["..."],
  "edges": ["..."],
  "initial_state": {"..."},
  "start": "..."
}
```

For JSON-based schemas, you need to import all node classes before initializing the WorkflowEngine. 
{: .important}

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

The conversion between path and id is simple: dots in IDs become slashes in paths, making **workflows.data_pipeline** equal to **workflows/data_pipeline.json**.
{: .note}

## Defining Your Workflow's Entry Point

Every workflow needs a starting point. If you don't explicitly set one (not recommended), the engine will default to the first node in your list .

```python
# Explicitly setting the start node (recommended)
engine = WorkflowEngine(
    nodes=[node1, node2, node3],
    start=node2  # We're starting with node2, not node1
)

# Without setting start - will use the first node in the list
engine = WorkflowEngine(nodes=[node1, node2, node3])  # Will start with node1
```

## Ready, Set, Start!: Baby Steps or Full Speed

The engine gives you two ways to run your workflow:

### Take One Step at a Time

Perfect for debugging or when you need granular control:

```python
# Execute just one node and stop
await engine.step()
```

### Full Speed Ahead

When you're ready to let it rip:

```python
# Run the entire workflow until completion or until input is required
await engine.run()
```
> For providing inputs when a node awaits `request_input()`, both the `step()` and `run()` functions take in a optional parameter called `input_data`. Check out [Human-in-the-Loop](../Advanced/Human_in_the_loop) for a more detailed explanation.
{: .note}

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

# Check if the workflow is waiting for user input
if engine.execution_state.workflow_status == WorkflowStatus.WAITING_FOR_INPUT:
    input_request = engine.execution_state.awaiting_input
    node_id = input_request['node_id']
    prompt = input_request['prompt']
    
    print(f"Workflow is asking: {prompt}")
    
    # Provide the requested input and continue
    user_response = input("> ")
    continuing = await engine.run({node_id: user_response})
```

The engine also maintains a complete history in `tracking_data` (we cover this in more detail in the next section), which captures the entire journey of your workflow for analysis and resumability.

Enjoy running your workflows! With Grapheteria's powerful engine, you can orchestrate complex state machines with confidence and control.
