from core.machine import WorkflowEngine, WorkflowStatus
import asyncio
from fastapi import APIRouter, HTTPException, Body
from pydantic import BaseModel
from typing import Dict, Any, Optional
import uvicorn

from core.storage import SQLiteStorage

router = APIRouter()

class CreateWorkflow(BaseModel):
    workflow_id: str

class WorkflowRequest(BaseModel):
    workflow_id: Optional[str]
    run_id: Optional[str]
    input_data: Optional[Dict[str, Any]] = None
    resume_from: Optional[int] = None
    fork: Optional[bool] = False

@router.post("/workflows/create")
async def create_workflow(request: CreateWorkflow):
    try:
        workflow_id = request.workflow_id
        workflow = WorkflowEngine(workflow_id=workflow_id)
        
        run_id = workflow.run_id
        print(workflow.execution_state)
        return {
            "run_id": run_id,
            "message": "Workflow successfully created",
            "execution_state": workflow.execution_state
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to start workflow: {str(e)}")

@router.post("/workflows/step")
async def step_workflow(request: WorkflowRequest):
    workflow_id, run_id, input_data, resume_from, fork = request.workflow_id, request.run_id, request.input_data, request.resume_from, request.fork

    print(f"Stepping workflow {workflow_id} with run_id {run_id} and resume_from {resume_from}")

    workflow = WorkflowEngine(workflow_id=workflow_id, run_id=run_id, resume_from=resume_from, fork=fork)

    task = asyncio.create_task(workflow.step(input_data=input_data))
    #Immediately start the task
    try:
        await asyncio.sleep(0)
        while workflow.execution_state.workflow_status == WorkflowStatus.RUNNING:
            await asyncio.sleep(0)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to step workflow: {str(e)}")
        
    return {    
        "run_id": run_id,
        "message": "Workflow stepped",
        "execution_state": workflow.execution_state
    }