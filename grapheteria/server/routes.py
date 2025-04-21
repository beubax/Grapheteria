from grapheteria import WorkflowEngine
from fastapi import APIRouter, HTTPException, Body
from typing import Dict, Any, Optional
from grapheteria.utils import FileSystemStorage

router = APIRouter()


@router.get("/workflows/create/{workflow_id}")
async def create_workflow(workflow_id: str):
    try:
        workflow = WorkflowEngine(workflow_id=workflow_id)

        run_id = workflow.run_id

        return {
            "message": "Workflow created",
            "run_id": run_id,
            "execution_data": workflow.tracking_data,
        }
    except Exception as e:
        print(e)
        raise HTTPException(
            status_code=500, detail=f"Failed to start workflow: {str(e)}"
        )


@router.post("/workflows/step/{workflow_id}/{run_id}")
async def step_workflow(
    workflow_id: str,
    run_id: str,
    input_data: Optional[Dict[str, Any]] = Body(None),
    resume_from: Optional[int] = Body(None),
    fork: bool = Body(False),
):
    # Create new workflow with specified parameters
    workflow = WorkflowEngine(
        workflow_id=workflow_id, run_id=run_id, resume_from=resume_from, fork=fork
    )

    try:
        await workflow.step(input_data=input_data)
    except Exception:
        # Just catch the exception, don't return here
        pass

    # Return response regardless of whether an exception occurred
    return {"message": "Workflow stepped", "execution_data": workflow.tracking_data}


@router.post("/workflows/run/{workflow_id}/{run_id}")
async def run_workflow(
    workflow_id: str,
    run_id: str,
    input_data: Optional[Dict[str, Any]] = Body(None),
    resume_from: Optional[int] = Body(None),
    fork: bool = Body(False),
):
    # Create new workflow with specified parameters
    workflow = WorkflowEngine(
        workflow_id=workflow_id, run_id=run_id, resume_from=resume_from, fork=fork
    )

    try:
        await workflow.run(input_data=input_data)
    except Exception:
        # Just catch the exception, don't return here
        pass

    return {"message": "Workflow run", "execution_data": workflow.tracking_data}


@router.get("/logs")
async def get_logs():
    return FileSystemStorage().list_workflows()


@router.get("/logs/{workflow_id}")
async def get_workflow_logs(workflow_id: str):
    return FileSystemStorage().list_runs(workflow_id)


@router.get("/logs/{workflow_id}/{run_id}")
async def get_run_logs(workflow_id: str, run_id: str):
    return FileSystemStorage().load_state(workflow_id, run_id)
