from grapheteria import WorkflowEngine, WorkflowStatus
import asyncio
from fastapi import APIRouter, HTTPException, Body
from pydantic import BaseModel
from typing import Dict, Any, Optional
from grapheteria.utils import FileSystemStorage

router = APIRouter()

# Dictionary to store active workflows
active_workflows = {}

@router.get("/workflows/create/{workflow_id}")
async def create_workflow(workflow_id: str):
    try:
        workflow = WorkflowEngine(workflow_id=workflow_id)
        
        run_id = workflow.run_id
        # Store workflow in active_workflows dictionary
        active_workflows[(workflow_id, run_id)] = workflow
        
        return {    
            "message": "Workflow created",
            "run_id": run_id,
            "execution_data": workflow.tracking_data
        }
    except Exception as e:
        print(e)
        raise HTTPException(status_code=500, detail=f"Failed to start workflow: {str(e)}")

@router.post("/workflows/step/{workflow_id}/{run_id}")
async def step_workflow(
    workflow_id: str, 
    run_id: str, 
    input_data: Optional[Dict[str, Any]] = Body(None),
    resume_from: Optional[int] = Body(None),
    fork: bool = Body(False)
):
    # Check if workflow exists in cache and resume_from and fork are None
    if resume_from is None and fork is False and (workflow_id, run_id) in active_workflows:
        workflow = active_workflows[(workflow_id, run_id)]
    else:
        # Create new workflow with specified parameters
        workflow = WorkflowEngine(workflow_id=workflow_id, run_id=run_id, resume_from=resume_from, fork=fork)
        # Store in cache
        active_workflows[(workflow_id, run_id)] = workflow

    _ = asyncio.create_task(workflow.step(input_data=input_data))
    
    try:
        await asyncio.sleep(0)
        while workflow.execution_state.workflow_status in [WorkflowStatus.RUNNING]:
            await asyncio.sleep(0)
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to step workflow: {str(e)}")
        
    return {    
        "message": "Workflow stepped",
        "execution_data": workflow.tracking_data
    }


@router.post("/workflows/run/{workflow_id}/{run_id}")
async def run_workflow(
    workflow_id: str, 
    run_id: str, 
    input_data: Optional[Dict[str, Any]] = Body(None),
    resume_from: Optional[int] = Body(None),
    fork: bool = Body(False)
):
    # Check if workflow exists in cache and resume_from and fork are None
    if resume_from is None and fork is False and (workflow_id, run_id) in active_workflows:
        workflow = active_workflows[(workflow_id, run_id)]
    else:
        # Create new workflow with specified parameters
        workflow = WorkflowEngine(workflow_id=workflow_id, run_id=run_id, resume_from=resume_from, fork=fork)
        # Store in cache
        active_workflows[(workflow_id, run_id)] = workflow

    _ = asyncio.create_task(workflow.run(input_data=input_data))
    
    try:
        await asyncio.sleep(0)
        while workflow.execution_state.workflow_status in [WorkflowStatus.RUNNING, WorkflowStatus.HEALTHY]:
            await asyncio.sleep(0)
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to run workflow: {str(e)}")
        
    return {    
        "message": "Workflow run",
        "execution_data": workflow.tracking_data
    }

@router.get("/logs")
async def get_logs():
    return FileSystemStorage().list_workflows()

@router.get("/logs/{workflow_id}")
async def get_workflow_logs(workflow_id: str):
    return FileSystemStorage().list_runs(workflow_id)

@router.get("/logs/{workflow_id}/{run_id}")
async def get_run_logs(workflow_id: str, run_id: str):
    return FileSystemStorage().load_state(workflow_id, run_id)