# Edge Class Documentation

## Overview

Edges are the connections between nodes in your workflow graph. They determine how your workflow transitions from one node to another, acting as pathways for execution flow. Without edges, your nodes would be isolated islands of functionality with no way to reach each other. Each edge has access to the workflow's shared communication state, allowing for dynamic routing decisions based on your data.

```python
# Creating an edge between two nodes
start_node > process_node > end_node
```

## Conditions

Edges can have conditions that determine whether they should be traversed. These conditions are Python expressions (as strings) that evaluate to `True` or `False` based on the current workflow's shared state.

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