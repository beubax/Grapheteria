---
layout: default
title: "Logging"
parent: "Core"
nav_order: 5
---

# Persistence and Time Travel

## Overview

You've already met the building blocks of our workflow engine - nodes, edges, shared variables, and the engine itself. But there's more to this story! Our workflow engine doesn't just execute steps and forget them. It's like a time traveler with a detailed journal - recording every step, allowing you to pause journeys, resume them later, or even create alternate timelines. Let's see how this magic works.

## Run IDs: Your Workflow's Passport

When a workflow starts its journey, it gets a unique passport - a run ID:

```python
engine = WorkflowEngine(
    nodes=[start_node, process_node, end_node],
    start=start_node
)
# A unique run_id like '20230615_143022_789' is auto-generated
print(f"Remember this ID to resume later: {engine.run_id}")
```

This ID is your ticket back to this exact workflow state. Store it somewhere safe if you want to return to this journey later!

> By default, logs are stored in the `logs` directory of your current working directory. You can examine these logs anytime to find historical run_ids. For a more user-friendly experience, all logs are also accessible through the UI where they're formatted and easier to navigate.
{: .note}

## Resuming Workflows: Pick Up Where You Left Off

Life happens. Servers restart. But your workflow can continue right where it paused:

```python
# Resume the workflow from the most recent step
resumed_engine = WorkflowEngine(
    workflow_id="my_awesome_workflow",
    run_id="20230615_143022_789"
)

# Or resume from a specific step
resumed_engine = WorkflowEngine(
    workflow_id="my_awesome_workflow",
    run_id="20230615_143022_789",
    resume_from=3  # Resume from step 3
)
```

The engine automatically loads the state and prepares to continue execution - whether it was waiting for input or ready to process the next node.

## Forking Workflows: Creating Alternate Timelines

Want to experiment with different paths without losing your original journey? Fork it!

```python
# Create a new branch from step 3 of a previous run
forked_engine = WorkflowEngine(
    workflow_id="my_awesome_workflow",
    run_id="20230615_143022_789",
    resume_from=3,
    fork=True  # This creates a new run_id and preserves the original
)
```

This creates a parallel universe - your original workflow remains intact while you explore a different path from the same starting point.

## State Validation: Keeping Your Timeline Consistent

Time travel can be messy. To prevent paradoxes, the engine validates that your current workflow definition is compatible with the saved state:

```python
try:
    # This will fail if 'critical_node' from step 5 is missing
    resumed_engine = WorkflowEngine(
        workflow_id="my_awesome_workflow",
        run_id="20230615_143022_789",
        resume_from=5
    )
except ValueError as e:
    print(f"Can't resume: {e}")  # "Cannot resume: Node 'critical_node' is missing..."
```

You can add new nodes to the future, but you can't erase the past - nodes that were already processed or waiting must exist in your current workflow.

## Storage Configuration: Beyond Local Files

By default, your workflow's history is stored in the local filesystem - perfect for development:

```python
# Default storage uses local filesystem
engine = WorkflowEngine(nodes=[...])

# For production, configure a different storage backend
from storage_backend import PostgresStorage
engine = WorkflowEngine(
    nodes=[...],
    storage_backend=PostgresStorage(connection_string="postgresql://...")
)
```

For more robust production environments, check out [our Storage Configuration guide](../Advanced/Extending_Logging) for options like database storage, cloud storage, and more.

Now you're ready to build workflows that can pause, resume, and even branch into different timelines. Happy time traveling!
