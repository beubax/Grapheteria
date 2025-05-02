#!/usr/bin/env python3
import asyncio
import json
import os
from orchestrator import TaskOrchestrator

# Set your Claude API key in the environment or pass it directly
# os.environ["CLAUDE_API_KEY"] = "your_api_key_here"

async def main():
    # Initialize the orchestrator
    orchestrator = TaskOrchestrator(
        workflows_dir="example_workflows",  # Custom directory for workflows
        storage_dir="example_logs"          # Custom directory for logs
    )
    
    # Create a new workflow
    workflow_name = "hello_world"
    task_description = """
    Create a simple workflow that:
    1. Asks the user for their name
    2. Greets the user
    3. Asks if they want to see the current time
    4. If yes, shows the current time, if no, thanks them for using the workflow
    """
    
    try:
        workflow_dir = orchestrator.create_workflow(
            workflow_name=workflow_name,
            task_description=task_description,
            overwrite=True  # Overwrite if it already exists
        )
        print(f"Created workflow at: {workflow_dir}")
    except Exception as e:
        print(f"Error creating workflow: {e}")
        return
    
    # List available workflows
    workflows = orchestrator.list_workflows()
    print(f"Available workflows: {workflows}")
    
    # Run the workflow
    print("\nRunning workflow...")
    result = await orchestrator.run_workflow(workflow_name=workflow_name)
    
    print(f"Run ID: {result['run_id']}")
    print(f"Status: {result['status']}")
    
    # If the workflow is waiting for input, provide it
    if result["awaiting_input"]:
        request_id = result["awaiting_input"]["request_id"]
        prompt = result["awaiting_input"]["prompt"]
        
        print(f"\nWorkflow is asking: {prompt}")
        user_input = input("> ")
        
        # Provide the input and continue running
        input_data = {request_id: user_input}
        result = await orchestrator.run_workflow(
            workflow_name=workflow_name,
            run_id=result["run_id"],
            input_data=input_data
        )
        
        # If it asks for more input, handle it again
        if result["awaiting_input"]:
            request_id = result["awaiting_input"]["request_id"]
            prompt = result["awaiting_input"]["prompt"]
            
            print(f"\nWorkflow is asking: {prompt}")
            user_input = input("> ")
            
            input_data = {request_id: user_input}
            result = await orchestrator.run_workflow(
                workflow_name=workflow_name,
                run_id=result["run_id"],
                input_data=input_data
            )
    
    # Check final workflow status
    if result["status"] == "COMPLETED":
        print("\nWorkflow completed successfully!")
        print("Final state:")
        print(json.dumps(result["shared_state"], indent=2))
    else:
        print(f"\nWorkflow status: {result['status']}")

if __name__ == "__main__":
    asyncio.run(main()) 