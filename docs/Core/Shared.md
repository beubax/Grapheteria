---
layout: default
title: "Communication"
parent: "Core"
nav_order: 3
---

# Shared: The Communication Protocol

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
initial_shared_state={
        "chat_history": [],
        "processing_results": [],
        "retry_count": 0,
        "last_execution_time": None
    }
```

Remember that the shared dictionary is meant for dynamic values that change as your workflow runs. For fixed inputs, use node configuration parameters instead.

Setting the same initial state in JSON which can be used with .... yeah yeah the UI, you get it.

```json
{
  "nodes": ["..."],
  "edges": ["..."],
  "initial_state": {
    "user_profile": {
      "name": "Alice",
      "preferences": ["quick", "automated"]
    } } }
```

## Serialization Superpowers

Now with the magic of Python pickling (via dill), your shared dictionary can store almost any Python object! Unlike before, you're no longer limited to JSON-friendly types:

- Complex objects: queues, custom classes, trained ML models
- Function references and callables
- Basically anything Python can create

```python
# ✅ Go wild with complex objects
from queue import Queue
import sklearn.linear_model

# Pass messages between nodes with queues
shared["task_queue"] = Queue()
shared["task_queue"].put({"priority": "high", "task": "analyze_data"})

# Share trained ML models between nodes
model = sklearn.linear_model.LinearRegression()
model.fit([[0], [1], [2]], [0, 1, 2])  # Train it
shared["prediction_model"] = model     # Store it

# ✅ Even store functions for maximum flexibility
def calculate_score(data):
    return sum(data) / len(data)
    
shared["scoring_function"] = calculate_score
```

This opens up powerful patterns: passing trained models between nodes, creating inter-node communication channels, or even building responsive agent networks that collaborate through shared resources.

By default, these serialized states are stored in your local filesystem. Need to persist to a database instead? Check out our [Extending Storage](../Advanced/Extending_Logging) guide.