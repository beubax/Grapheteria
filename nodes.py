from machine import Node, WorkflowEngine, NodeStatus
import asyncio
import json
import random
from fastapi import FastAPI, HTTPException, Body
from pydantic import BaseModel
from typing import Dict, Any, Optional, List
import uvicorn

class AgentNode(Node):
    async def prepare(self, _, queue):
        message = "Hello from agent node!"
        return message
        
    async def execute(self, prepared_result):
        # Required implementation of abstract method
        return prepared_result
    
    async def cleanup(self, shared, prepared_result, execution_result):
        shared["messages"].append("Agent NODE")

class TestNode(Node):
    async def prepare(self, _, request_input):
        res = await request_input()
        return res
        
    def execute(self, prepared_result):
        # Required implementation of abstract method
        return prepared_result
    
    def cleanup(self, shared, prepared_result, execution_result):
        shared["messages"].append(prepared_result)

# Store active workflows by their ID
active_workflows = {}

# Store workflow tasks by their ID
workflow_tasks = {}

app = FastAPI()

class WorkflowRequest(BaseModel):
    workflow_path: str
    run_id: Optional[str] = None
    input_data: Optional[Dict[str, Any]] = None

class InputRequest(BaseModel):
    workflow_id: str
    input_data: Dict[str, Any]

async def run_workflow_task(workflow_id: str, workflow: WorkflowEngine, input_data: Optional[Dict[str, Any]] = None):
    """Run workflow as a background task"""
    try:
        result = await workflow.run(input_data=input_data)
        
        # If workflow completes, mark for cleanup
        if not result["is_active"]:
            # Keep workflow in active_workflows for a while to allow status queries
            # In a production system, you might want to implement cleanup after some time
            pass
            
    except Exception as e:
        print(f"Workflow {workflow_id} failed: {str(e)}")
        # You could update some status here if needed

@app.post("/workflows/start")
async def start_workflow(request: WorkflowRequest):
    try:
        workflow = WorkflowEngine(json_path=request.workflow_path, run_id=request.run_id)
        
        # Store the workflow instance for future requests
        workflow_id = workflow.run_id
        active_workflows[workflow_id] = workflow
        
        # Start workflow execution as a background task
        task = asyncio.create_task(run_workflow_task(workflow_id, workflow, request.input_data))
        
        # Return immediately with initial workflow info
        return {
            "workflow_id": workflow_id,
            "status": "RUNNING",
            "is_active": True,
            "message": "Workflow started as background task"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to start workflow: {str(e)}")

@app.post("/workflows/input")
async def provide_input(request: InputRequest):
    workflow_id = request.workflow_id
    
    if workflow_id not in active_workflows:
        raise HTTPException(status_code=404, detail=f"Workflow {workflow_id} not found")
    
    workflow = active_workflows[workflow_id]
    
    if workflow.execution_state.workflow_status.name != "WAITING_FOR_INPUT":
        raise HTTPException(status_code=400, detail="Workflow is not waiting for input")
    
    try:
        # Create new task with the input data - using the same workflow instance
        # The workflow's internal future will be resolved with this input
        task = asyncio.create_task(run_workflow_task(workflow_id, workflow, request.input_data))
        
        return {
            "workflow_id": workflow_id,
            "status": "RUNNING",
            "is_active": True,
            "message": "Input provided, workflow continuing execution"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to process input: {str(e)}")

# Keep the original main function for reference or direct script execution
async def main():
    workflow = WorkflowEngine(json_path="workflow.json")
    
    # Run initial workflow
    task = asyncio.create_task(workflow.run())
    await asyncio.sleep(1)
    task = asyncio.create_task(workflow.run(input_data={"1741134227911": "Hello"}))
    await asyncio.sleep(1)

if __name__ == "__main__":
    # Run the main function directly
    asyncio.run(main())