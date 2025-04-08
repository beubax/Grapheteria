# Deploying Workflows with FastAPI

## Overview

Ready to share your workflows with the world? FastAPI makes it easy to deploy your Grapheteria workflows as a flexible API. Whether you're building an internal tool or a public service, these routes will help you manage workflow creation, execution, and monitoring.

First, let's create a simple workflow definition file that we can use in our API:

```python
# workflow_definitions.py
from grapheteria import Node, WorkflowEngine

class StartNode(Node):
    def execute(self, prepared_result):
        return "Hello from the start node!"

class ProcessNode(Node):
    def execute(self, prepared_result):
        return f"Processing data: {self.config.get('process_type', 'default')}"

class EndNode(Node):
    def execute(self, prepared_result):
        return "Workflow completed successfully!"

def create_sample_workflow():
    # Create nodes
    start = StartNode()
    process = ProcessNode(config={"process_type": "sample"})
    end = EndNode()
    
    # Connect nodes
    start > process > end
    
    # Create workflow with nodes and start node
    return WorkflowEngine(nodes=[start, process, end], start=start)
```

Here's the JSON equivalent of this workflow that could be stored as a file:

```json
{
  "nodes": [
    {
      "id": "start_node_1",
      "class": "StartNode"
    },
    {
      "id": "process_node_1",
      "class": "ProcessNode",
      "config": {
        "process_type": "sample"
      }
    },
    {
      "id": "end_node_1",
      "class": "EndNode"
    }
  ],
  "edges": [
    {
      "from": "start_node_1",
      "to": "process_node_1"
    },
    {
      "from": "process_node_1",
      "to": "end_node_1"
    }
  ],
  "start": "start_node_1"
}
```
*Note: This JSON could be created and exported using the Grapheteria UI.*

Now, let's set up our FastAPI app:

```python
from fastapi import FastAPI, HTTPException, Body
from grapheteria import WorkflowEngine, WorkflowStatus
from typing import Dict, Any, Optional
import asyncio
from workflow_definitions import create_sample_workflow

# Create FastAPI app
app = FastAPI(title="Grapheteria Workflows API")

# Dictionary to store active workflows
active_workflows = {}
```

## Creating Workflows

Create a new workflow instance with this route:

```python
@app.get("/workflows/create/{workflow_id}")
async def create_workflow(workflow_id: str):
    try:
        # Create workflow from JSON definition
        workflow = WorkflowEngine(workflow_id=workflow_id)
        
        # Note: You could also create a workflow from code:
        # workflow = create_sample_workflow()
        
        # Get the run ID and store workflow in memory
        run_id = workflow.run_id
        active_workflows[(workflow_id, run_id)] = workflow
        
        return {    
            "message": "Workflow created",
            "run_id": run_id,
            "execution_data": workflow.tracking_data
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create workflow: {str(e)}")
```

This endpoint creates a workflow instance and returns a run_id you'll need for subsequent operations. Think of it as getting your boarding pass before a flight!

## Stepping Through a Workflow

Sometimes you want more control over execution. This route lets you step through one node at a time:

```python
@app.post("/workflows/step/{workflow_id}/{run_id}")
async def step_workflow(
    workflow_id: str, 
    run_id: str, 
    input_data: Optional[Dict[str, Any]] = Body(None),
    resume_from: Optional[int] = Body(None),
    fork: bool = Body(False)
):
    # Either get existing workflow or create new one
    if resume_from is None and not fork and (workflow_id, run_id) in active_workflows:
        workflow = active_workflows[(workflow_id, run_id)]
    else:
        workflow = WorkflowEngine(
            workflow_id=workflow_id, 
            run_id=run_id, 
            resume_from=resume_from, 
            fork=fork
        )
        active_workflows[(workflow_id, run_id)] = workflow

    # Execute a single step
    try:
        continuing, tracking_data = await workflow.step(input_data=input_data)
        
        return {    
            "message": "Workflow stepped",
            "continuing": continuing,
            "execution_data": tracking_data
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Step failed: {str(e)}")
```

Perfect for cautious workflows or when you need to process each node's results separately.

## Running a Complete Workflow

When you're ready to let your workflow run until completion or until it needs input:

```python
@app.post("/workflows/run/{workflow_id}/{run_id}")
async def run_workflow(
    workflow_id: str, 
    run_id: str, 
    input_data: Optional[Dict[str, Any]] = Body(None),
    resume_from: Optional[int] = Body(None),
    fork: bool = Body(False)
):
    # Get existing or create new workflow
    if resume_from is None and not fork and (workflow_id, run_id) in active_workflows:
        workflow = active_workflows[(workflow_id, run_id)]
    else:
        workflow = WorkflowEngine(
            workflow_id=workflow_id, 
            run_id=run_id, 
            resume_from=resume_from, 
            fork=fork
        )
        active_workflows[(workflow_id, run_id)] = workflow

    # Run until completion or waiting for input
    try:
        continuing, tracking_data = await workflow.run(input_data=input_data)
        
        return {    
            "message": "Workflow run",
            "continuing": continuing,
            "execution_data": tracking_data,
            "status": workflow.execution_state.workflow_status.name
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Execution failed: {str(e)}")
```

Set it and forget it! Your workflow runs until it needs input or reaches its destination.

## Additional Useful Routes

### Getting Workflow Status

```python
@app.get("/workflows/status/{workflow_id}/{run_id}")
async def get_workflow_status(workflow_id: str, run_id: str):
    """Check the current status of a workflow"""
    try:
        # Load the workflow directly with WorkflowEngine
        workflow = WorkflowEngine(workflow_id=workflow_id, run_id=run_id)
        
        return {
            "status": workflow.execution_state.workflow_status.name,
            "awaiting_input": workflow.execution_state.awaiting_input,
            "current_node": workflow.execution_state.next_node_id
        }
    except Exception as e:
        raise HTTPException(status_code=404, detail=f"Workflow not found: {str(e)}")
    
    # Note: Alternatively, we could load directly from storage logs
    # storage = FileSystemStorage()
    # state = storage.load_state(workflow_id, run_id)
```

Perfect for checking if your workflow is lounging on the beach or hard at work.

### Viewing Workflow Logs

Get insights into your workflows with these logging endpoints:

```python
@app.get("/logs")
async def get_logs():
    """List all available workflows"""
    from grapheteria.utils import FileSystemStorage
    storage = FileSystemStorage()
    return storage.list_workflows()

@app.get("/logs/{workflow_id}")
async def get_workflow_logs(workflow_id: str):
    """List all runs for a specific workflow"""
    from grapheteria.utils import FileSystemStorage
    storage = FileSystemStorage()
    return storage.list_runs(workflow_id)

@app.get("/logs/{workflow_id}/{run_id}")
async def get_run_logs(workflow_id: str, run_id: str):
    """Get full execution history for a specific run"""
    from grapheteria.utils import FileSystemStorage
    storage = FileSystemStorage()
    return storage.load_state(workflow_id, run_id)
```

These routes let you peek under the hood to see what your workflows have been up to.

## Running Your API

With these routes in place, you can launch your API server:

```python
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
```

Now your workflows are ready for the big time! Access them via HTTP requests from any application or try them out using FastAPI's automatic Swagger UI at `http://localhost:8000/docs`.

For more details on deploying your FastAPI application to production, check out the [FastAPI deployment documentation](https://fastapi.tiangolo.com/deployment/).
