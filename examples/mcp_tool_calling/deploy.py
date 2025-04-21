from fastapi import FastAPI, HTTPException
from typing import Optional
from pydantic import BaseModel

# Import our workflow components
from grapheteria import WorkflowEngine
# Import nodes to ensure they're registered
from examples.a2a.flow import *

app = FastAPI(title="MCP Tool-Calling API")

# Store for active workflows
active_workflows = {}

# Models for request validation
class InputData(BaseModel):
    input_value: str

@app.post("/workflows/create")
async def create_workflow():
    """Create a new tool-calling workflow instance"""
    try:
        workflow = WorkflowEngine(workflow_path="workflow.json")
        run_id = workflow.run_id
        active_workflows[run_id] = workflow
        
        return {
            "message": "MCP Tool-calling workflow created",
            "run_id": run_id,
            "status": workflow.execution_state.workflow_status.name
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create workflow: {str(e)}")

@app.post("/workflows/run/{run_id}")
async def step_workflow(run_id: str, input_data: Optional[InputData] = None):
    """Execute one step of the workflow - handles inputs when needed"""
    if run_id not in active_workflows:
        raise HTTPException(status_code=404, detail="Workflow not found")
    
    workflow = active_workflows[run_id]
    
    try:
        # If workflow is waiting for input and we have input
        if workflow.execution_state.awaiting_input and input_data:
            node_id = workflow.execution_state.awaiting_input["request_id"]
            input_value = input_data.input_value

            await workflow.run({node_id: input_value})
        else:
            # Step without input
            await workflow.run()
        
        # Prepare the response
        response = {
            "status": workflow.execution_state.workflow_status.name,
        }
        
        # Include final response if available
        if "final_response" in workflow.execution_state.shared:
            response["answer"] = workflow.execution_state.shared["final_response"]
        
        # Include question if available
        if "question" in workflow.execution_state.shared:
            response["question"] = workflow.execution_state.shared["question"]
        
        # Include tool call information if available
        if "tool_calls" in workflow.execution_state.shared:
            response["tool_calls"] = workflow.execution_state.shared["tool_calls"]
        
        # Include input request if waiting for input
        if workflow.execution_state.awaiting_input:
            response["awaiting_input"] = workflow.execution_state.awaiting_input
            
        return response
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Workflow step failed: {str(e)}")

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
        "awaiting_input": workflow.execution_state.awaiting_input
    }

@app.get("/workflows/results/{run_id}")
async def get_workflow_results(run_id: str):
    """Get the current results from the workflow"""
    if run_id not in active_workflows:
        raise HTTPException(status_code=404, detail="Workflow not found")
    
    workflow = active_workflows[run_id]
    shared = workflow.execution_state.shared
    
    # Extract the important information
    result = {
        "status": workflow.execution_state.workflow_status.name,
    }
    
    # Add relevant parts of the shared state
    if "question" in shared:
        result["question"] = shared["question"]
    if "final_response" in shared:
        result["answer"] = shared["final_response"]
    if "tool_calls" in shared:
        result["tool_calls"] = shared["tool_calls"]
    
    return result

@app.delete("/workflows/{run_id}")
async def delete_workflow(run_id: str):
    """Delete a workflow instance"""
    if run_id not in active_workflows:
        raise HTTPException(status_code=404, detail="Workflow not found")
    
    del active_workflows[run_id]
    return {"message": f"Workflow {run_id} deleted successfully"}

# Run the server
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
