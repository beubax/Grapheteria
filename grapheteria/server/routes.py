from grapheteria import WorkflowEngine
from fastapi import APIRouter, HTTPException, Body
from typing import Dict, Any, List, Optional
from grapheteria.utils import FileSystemStorage
from grapheteria.server.workflow_manager import WorkflowManager
from grapheteria.toolregistry import ToolRegistry
def get_router(workflow_manager: WorkflowManager):
    router = APIRouter()

    def get_consolidated_registry(tool_registry: Dict[str, ToolRegistry]) -> ToolRegistry:
        consolidated_registry = ToolRegistry()
        for (url, registry) in tool_registry.values():
            consolidated_registry.merge(registry)
        return consolidated_registry

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
        registry = get_consolidated_registry(workflow_manager.tool_registry)

        # Create new workflow with specified parameters
        workflow = WorkflowEngine(
            workflow_id=workflow_id, run_id=run_id, resume_from=resume_from, fork=fork, tool_registry=registry
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
        registry = get_consolidated_registry(workflow_manager.tool_registry)

        # Create new workflow with specified parameters
        workflow = WorkflowEngine(
            workflow_id=workflow_id, run_id=run_id, resume_from=resume_from, fork=fork, tool_registry=registry
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
    
    @router.post("/workflows/create")
    async def create_workflow(
        data: Dict[str, Any] = Body(...)
    ):
        try:
            # Extract parameters from the request body
            workflow_name = data.get("workflow_name")
            create_description = data.get("create_description")

            if workflow_name in workflow_manager.workflows:
                return {"message": "Workflow already exists"}
            
            if create_description == "":
                create_description = None
            
            registry = get_consolidated_registry(workflow_manager.tool_registry)
            
            # Update the workflow
            _ = WorkflowEngine.create_workflow(
                workflow_id=workflow_name,
                create_description=create_description,
                tool_registry=registry
            )
            
            return {"message": "I have successfully created the workflow!"}
        except Exception as e:
            print(f"Error creating workflow: {str(e)}")
            raise HTTPException(
                status_code=500,
                detail=f"Failed to create workflow: {str(e)}"
            )

    @router.post("/workflows/update/{workflow_id}")
    async def update_workflow(
        workflow_id: str, 
        data: Dict[str, Any] = Body(...)
    ):
        try:
            # Extract parameters from the request body
            update_description = data.get("update_description")
            
            # Validate required parameters
            if not update_description:
                return {"message": "Enter a description to update the workflow"}
            
            registry = get_consolidated_registry(workflow_manager.tool_registry)
            
            # Update the workflow
            _ = WorkflowEngine.update_workflow(
                workflow_id=workflow_id,
                update_description=update_description,
                tool_registry=registry
            )
            
            return {"message": "I have successfully updated the workflow!"}
        except Exception as e:
            print(f"Error updating workflow: {str(e)}")
            raise HTTPException(
                status_code=500,
                detail=f"Failed to update workflow: {str(e)}"
            )
        
    @router.post("/add_mcp")
    async def add_mcp(
        data: Dict[str, Any] = Body(...)
    ):
        mcp_name = data.get("mcp_name")
        mcp_url = data.get("mcp_url")

        return workflow_manager.add_mcp_to_registry(mcp_name, mcp_url)

    @router.post("/remove_mcp")
    async def remove_mcp(
        data: Dict[str, Any] = Body(...)
    ):
        mcp_name = data.get("mcp_name")
        return workflow_manager.remove_mcp_from_registry(mcp_name)
    
    @router.post("/update_mcp_url")
    async def update_mcp_url(
        data: Dict[str, Any] = Body(...)
    ):
        mcp_name = data.get("mcp_name")
        mcp_url = data.get("mcp_url")
        return workflow_manager.update_mcp_url(mcp_name, mcp_url)
    
    @router.post("/refresh_mcp_tool")
    async def refresh_mcp_tool(
        data: Dict[str, Any] = Body(...)
    ):
        mcp_name = data.get("mcp_name")
        return workflow_manager.refresh_mcp_tool(mcp_name)
    
    return router