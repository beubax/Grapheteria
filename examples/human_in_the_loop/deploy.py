from fastapi import FastAPI, HTTPException
from typing import Optional
from pydantic import BaseModel

# Import our workflow components
from grapheteria import WorkflowEngine
# Do not forget to import your nodes since we are utilizing the JSON schema!
from nodes import *
# Create FastAPI app
app = FastAPI(title="AI Content Creation API")

# Store for active workflows
active_workflows = {}

# Models for request validation
class InputData(BaseModel):
    input_value: str

# Routes for workflow interaction
@app.post("/workflows/create")
async def create_workflow():
    """Create a new content creation workflow instance"""
    try:
        workflow = WorkflowEngine(workflow_path="workflow.json")
        run_id = workflow.run_id
        active_workflows[run_id] = workflow
        
        return {
            "message": "Content workflow created",
            "run_id": run_id,
            "status": workflow.execution_state.workflow_status
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create workflow: {str(e)}")

@app.post("/workflows/run/{run_id}")
async def step_workflow(run_id: str, input_data: Optional[InputData] = None):
    """Execute one step of the workflow - used when input is needed"""
    if run_id not in active_workflows:
        raise HTTPException(status_code=404, detail="Workflow not found")
    
    workflow = active_workflows[run_id]
    
    try:
        # If the workflow is waiting for input and we provided input
        if workflow.execution_state.awaiting_input and input_data:
            node_id = workflow.execution_state.awaiting_input["node_id"]
            input_value = input_data.input_value
            
            # Step with provided input
            await workflow.run({node_id: input_value})
        else:
            # Step without input
            await workflow.run()
        
        # Prepare response
        response = {
            "status": workflow.execution_state.workflow_status,
            "article": workflow.execution_state.shared.get("content")
        }
        
        # If workflow is waiting for input, include that info
        if workflow.execution_state.awaiting_input:
            response["awaiting_input"] = workflow.execution_state.awaiting_input
            
        return response
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Step failed: {str(e)}")

@app.get("/workflows/status/{run_id}")
async def get_workflow_status(run_id: str):
    """Check the current status of a workflow"""
    if run_id not in active_workflows:
        raise HTTPException(status_code=404, detail="Workflow not found")
    
    workflow = active_workflows[run_id]
    
    # Extract the important information
    return {
        "status": workflow.execution_state.workflow_status,
        "current_node": workflow.execution_state.next_node_id,
        "awaiting_input": workflow.execution_state.awaiting_input,
        "shared_state": workflow.execution_state.shared
    }

# Run the server
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)