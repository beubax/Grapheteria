from machine import Node, WorkflowEngine, WorkflowStatus
import asyncio
from fastapi import FastAPI, HTTPException, Body
from pydantic import BaseModel
from typing import Dict, Any, Optional
import uvicorn

class AgentNode(Node):
    async def prepare(self, _, request_input):
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

app = FastAPI()

class CreateWorkflow(BaseModel):
    workflow_path: str

class WorkflowRequest(BaseModel):
    workflow_path: str
    run_id: str
    input_data: Optional[Dict[str, Any]] = None
    resume_from: Optional[int] = None
    fork: Optional[bool] = False

@app.get("/workflows/create")
async def create_workflow(request: CreateWorkflow):
    try:
        workflow_path = request.workflow_path
        workflow = WorkflowEngine(json_path=workflow_path)
        
        run_id = workflow.run_id
        active_workflows[(workflow_path, run_id)] = workflow

        return {
            "run_id": run_id,
            "message": "Workflow successfully created",
            "execution_state": workflow.execution_state
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to start workflow: {str(e)}")
    
async def step_workflow(request: WorkflowRequest, active: bool = False):
    workflow_path, run_id, input_data, resume_from, fork = request.workflow_path, request.run_id, request.input_data, request.resume_from, request.fork

    if active:
        if (workflow_path, run_id) not in active_workflows:
            raise HTTPException(status_code=404, detail=f"Workflow {workflow_path} not found with run_id {run_id}")
        workflow = active_workflows[(workflow_path, run_id)]
    else:
        workflow = WorkflowEngine(json_path=workflow_path, run_id=run_id, resume_from=resume_from, fork=fork)

    task = asyncio.create_task(workflow.step(input_data=input_data))

    #Immediately start the task
    await asyncio.sleep(0)
    while workflow.execution_state.workflow_status == WorkflowStatus.RUNNING:
        await asyncio.sleep(0)

    return {
        "run_id": run_id,
        "message": "Workflow stepped",
        "execution_state": workflow.execution_state
    }
    
@app.post("/workflows/step_active")
async def step_workflow_active(request: WorkflowRequest):
    return await step_workflow(request, active=True)

@app.post("/workflows/step")
async def step_workflow(request: WorkflowRequest):
    return await step_workflow(request, active=False)

async def main():
    workflow = WorkflowEngine(workflow_id="workflow")
    await workflow.run()
if __name__ == "__main__":
    # Run the main function directly
    # uvicorn.run(app, host="0.0.0.0", port=8000)
    asyncio.run(main())