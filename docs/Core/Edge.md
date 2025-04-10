---
layout: default
title: "Edge"
parent: "Core"
nav_order: 2
---

# Connect your Nodes

## Overview

Edges are the connections between nodes in your workflow graph. They determine how your workflow transitions from one node to another. Without edges, your nodes would be isolated islands of functionality with no way to reach each other. Each edge has access to the workflow's shared [communication](./Shared) state, allowing for dynamic routing decisions based on your data.

```python
# Creating an edge between two nodes
start_node > process_node > end_node
```

## Conditions

Each edge in your workflow is a one-way street connecting two nodes with some conditions that determine when traffic can flow. These conditions are Python expressions (as strings) that evaluate to `True` or `False` based on the current workflow's shared state.

```python
# Edge with a condition
validate_node - "shared['score'] > 80" > success_node
validate_node - "shared['score'] <= 80" > retry_node
```

The default edge (with an empty string condition `""`) serves as a fallback path when no other conditions match. Conditions make your workflow dynamic, enabling complex branching logic.

## Order of Edge Condition Evaluation

When a node finishes execution, the system evaluates its outgoing edges in this order:

1. **True condition**: If any edge has the literal condition `"True"`, it's automatically selected regardless of other edges.
   ```python
   # This edge will always be taken
   special_node - "True" > priority_node
   ```

2. **Evaluated conditions**: The system evaluates each edge's condition against the shared state and selects the first one that returns `True`.
   ```python
   # First matching condition wins
   decision_node - "shared['temp'] > 30" > hot_handler
   decision_node - "shared['temp'] > 20" > warm_handler
   ```

3. **Default edge**: If no conditions match, the system uses the default edge (empty condition) as a fallback.
   ```python
   decision_node > default_handler  # Default edge (empty condition)
   ```

```python
# Complex condition example
analysis_node - "shared['status'] == 'urgent' and shared['priority'] > 5" > urgent_handler
analysis_node > standard_handler
```

Remember, edge conditions are the decision points in your workflow - they determine which path your data will travel!

## JSON Definition

While Python code is great for programmatically building workflows, you can also define edges in JSON. This is especially handy when working with the UI editor (Grapheteria's center of attraction!), which syncs with and can modify your JSON schema in real-time.

```json
{
  "edges": [
    {
      "from": "validate_node",
      "to": "success_node",
      "condition": "shared['score'] > 80"
    },
    {
      "from": "validate_node",
      "to": "retry_node",
      "condition": "shared['score'] <= 80"
    },
    {
      "from": "process_node",
      "to": "end_node"
    }
  ]
}
```

> Note that in JSON, the "from" and "to" fields are string IDs that reference nodes by their identifier, not the actual node objects as in code. This is a key difference between the two approaches. 
{: .important}

The last edge has no condition specified - it's our default edge! The JSON representation makes it easy to visualize your entire workflow structure in one place.

Now you're ready to connect your nodes any way you like - with code or JSON! Whether you're building a simple linear process or a complex decision tree, edges are your trusty pathways through the workflow jungle.