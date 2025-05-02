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
    
    # List available tools
    print("Available tools:")
    tools = orchestrator.list_available_tools()
    for tool_name in tools:
        tool_details = orchestrator.get_tool_details(tool_name)
        authenticated = "✓" if tool_details.get("authenticated", False) else "✗"
        print(f"  - {tool_name} ({authenticated})")
    
    # Authenticate with tools if needed
    for tool_name in ["gmail", "slack"]:
        tool_details = orchestrator.get_tool_details(tool_name)
        if not tool_details.get("authenticated", False):
            print(f"\nAuthenticating with {tool_name}...")
            success = orchestrator.authenticate_tool(tool_name)
            if success:
                print(f"Successfully authenticated with {tool_name}")
            else:
                print(f"Failed to authenticate with {tool_name}")
    
    # Create a new workflow with tools
    workflow_name = "email_summary"
    task_description = """
    Create a workflow that:
    1. Fetches the latest emails from Gmail
    2. Summarizes the content of each email
    3. Posts the summaries to a Slack channel
    4. Asks the user if they want to reply to any emails
    5. If yes, asks for the email selection and reply content, then sends the reply
    """
    
    try:
        workflow_dir = orchestrator.create_workflow(
            workflow_name=workflow_name,
            task_description=task_description,
            tools=["gmail", "slack"],
            overwrite=True  # Overwrite if it already exists
        )
        print(f"\nCreated workflow at: {workflow_dir}")
    except Exception as e:
        print(f"\nError creating workflow: {e}")
        return
    
    # List tools used by the workflow
    workflow_tools = orchestrator.get_workflow_tools(workflow_name)
    print(f"\nTools used by workflow '{workflow_name}':")
    for tool_name in workflow_tools:
        tool_details = orchestrator.get_tool_details(tool_name)
        authenticated = "✓" if tool_details.get("authenticated", False) else "✗"
        print(f"  - {tool_name} ({authenticated})")
    
    # Run the workflow
    print("\nRunning workflow...")
    result = await orchestrator.run_workflow(workflow_name=workflow_name)
    
    print(f"Run ID: {result['run_id']}")
    print(f"Status: {result['status']}")
    
    # If the workflow is waiting for input, provide it
    if result["awaiting_input"]:
        handle_workflow_input(orchestrator, workflow_name, result)
    
    # Print final status
    if result["status"] == "COMPLETED":
        print("\nWorkflow completed successfully!")
        # Don't print the tools field as it can be very verbose
        shared_state = result["shared_state"].copy()
        if "tools" in shared_state:
            del shared_state["tools"]
        print("Final state:")
        print(json.dumps(shared_state, indent=2))
    else:
        print(f"\nWorkflow status: {result['status']}")

async def handle_workflow_input(orchestrator, workflow_name, result):
    """Handle workflow input requests."""
    # We'll handle up to 3 input requests in this example
    for _ in range(3):
        if not result["awaiting_input"]:
            break
            
        request_id = result["awaiting_input"]["request_id"]
        prompt = result["awaiting_input"]["prompt"]
        
        print(f"\nWorkflow is asking: {prompt}")
        if result["awaiting_input"].get("options"):
            print("Options:")
            for i, option in enumerate(result["awaiting_input"]["options"]):
                print(f"  {i+1}. {option}")
        
        user_input = input("> ")
        
        # Provide the input and continue running
        input_data = {request_id: user_input}
        result = await orchestrator.run_workflow(
            workflow_name=workflow_name,
            run_id=result["run_id"],
            input_data=input_data
        )
    
    return result

if __name__ == "__main__":
    asyncio.run(main()) 