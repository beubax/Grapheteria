#!/usr/bin/env python3
import argparse
import asyncio
import json
import os
import sys
from typing import Dict, Any, Optional

from orchestrator import TaskOrchestrator


def setup_parser() -> argparse.ArgumentParser:
    """Set up the argument parser for the CLI."""
    parser = argparse.ArgumentParser(description="Grapheteria Workflow Orchestrator CLI")
    subparsers = parser.add_subparsers(dest="command", help="Command to execute")
    
    # Create workflow command
    create_parser = subparsers.add_parser("create", help="Create a new workflow")
    create_parser.add_argument("name", help="Workflow name")
    create_parser.add_argument("task", help="Task description")
    create_parser.add_argument("--tools", help="Comma-separated list of tools to include")
    create_parser.add_argument("--overwrite", action="store_true", help="Overwrite existing workflow")
    
    # Update workflow command
    update_parser = subparsers.add_parser("update", help="Update an existing workflow")
    update_parser.add_argument("name", help="Workflow name")
    update_parser.add_argument("update", help="Update description")
    update_parser.add_argument("--tools", help="Comma-separated list of tools to add")
    
    # List workflows command
    list_parser = subparsers.add_parser("list", help="List available workflows")
    
    # Run workflow command
    run_parser = subparsers.add_parser("run", help="Run a workflow")
    run_parser.add_argument("name", help="Workflow name")
    run_parser.add_argument("--input", help="JSON input data")
    run_parser.add_argument("--run-id", help="Run ID to resume")
    run_parser.add_argument("--step", type=int, help="Step to resume from")
    run_parser.add_argument("--fork", action="store_true", help="Fork execution")
    
    # Step workflow command
    step_parser = subparsers.add_parser("step", help="Step through a workflow")
    step_parser.add_argument("name", help="Workflow name")
    step_parser.add_argument("--input", help="JSON input data")
    step_parser.add_argument("--run-id", help="Run ID to resume")
    step_parser.add_argument("--step", type=int, help="Step to resume from")
    step_parser.add_argument("--fork", action="store_true", help="Fork execution")
    
    # List runs command
    runs_parser = subparsers.add_parser("runs", help="List runs for a workflow")
    runs_parser.add_argument("name", help="Workflow name")
    
    # List tools command
    tools_parser = subparsers.add_parser("list-tools", help="List available tools")
    
    # Get tool details command
    tool_details_parser = subparsers.add_parser("tool-details", help="Get details about a specific tool")
    tool_details_parser.add_argument("name", help="Tool name")
    
    # Authenticate tool command
    auth_parser = subparsers.add_parser("authenticate-tool", help="Authenticate with a tool")
    auth_parser.add_argument("name", help="Tool name")
    auth_parser.add_argument("--credentials", help="JSON credentials (if required)")
    
    # List workflow tools command
    workflow_tools_parser = subparsers.add_parser("workflow-tools", help="List tools used by a workflow")
    workflow_tools_parser.add_argument("name", help="Workflow name")
    
    return parser


async def main() -> None:
    """Main entry point for the CLI."""
    parser = setup_parser()
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    # Initialize the orchestrator
    orchestrator = TaskOrchestrator()
    
    # Parse input data if provided
    input_data = None
    if hasattr(args, "input") and args.input:
        try:
            input_data = json.loads(args.input)
        except json.JSONDecodeError:
            print(f"Error: Invalid JSON input: {args.input}")
            sys.exit(1)
    
    # Execute the appropriate command
    if args.command == "create":
        tools = args.tools.split(',') if args.tools else None
        
        try:
            workflow_dir = orchestrator.create_workflow(
                workflow_name=args.name,
                task_description=args.task,
                tools=tools,
                overwrite=args.overwrite
            )
            print(f"Workflow created at: {workflow_dir}")
            
            if tools:
                print("Included tools:")
                for tool in tools:
                    tool_details = orchestrator.get_tool_details(tool)
                    authenticated = "✓" if tool_details.get("authenticated", False) else "✗"
                    print(f"  - {tool} ({authenticated})")
        except FileExistsError as e:
            print(f"Error: {e}")
            sys.exit(1)
    
    elif args.command == "update":
        tools = args.tools.split(',') if args.tools else None
        
        try:
            workflow_dir = orchestrator.update_workflow(
                workflow_name=args.name,
                update_description=args.update,
                tools=tools
            )
            print(f"Workflow updated at: {workflow_dir}")
            
            if tools:
                print("Added tools:")
                for tool in tools:
                    tool_details = orchestrator.get_tool_details(tool)
                    authenticated = "✓" if tool_details.get("authenticated", False) else "✗"
                    print(f"  - {tool} ({authenticated})")
        except FileNotFoundError as e:
            print(f"Error: {e}")
            sys.exit(1)
    
    elif args.command == "list":
        workflows = orchestrator.list_workflows()
        if workflows:
            print("Available workflows:")
            for workflow in workflows:
                print(f"  - {workflow}")
        else:
            print("No workflows available.")
    
    elif args.command == "run":
        try:
            result = await orchestrator.run_workflow(
                workflow_name=args.name,
                input_data=input_data,
                run_id=args.run_id,
                resume_from=args.step,
                fork=args.fork
            )
            
            print(f"Run ID: {result['run_id']}")
            print(f"Status: {result['status']}")
            
            if result["awaiting_input"]:
                print("\nWorkflow is waiting for input:")
                print(f"  Node ID: {result['awaiting_input']['node_id']}")
                print(f"  Request ID: {result['awaiting_input']['request_id']}")
                print(f"  Prompt: {result['awaiting_input']['prompt']}")
                print(f"  Input Type: {result['awaiting_input']['input_type']}")
                if result['awaiting_input'].get('options'):
                    print(f"  Options: {result['awaiting_input']['options']}")
                
                print("\nTo provide input, use:")
                input_data = {result['awaiting_input']['request_id']: "YOUR_INPUT_HERE"}
                print(f'  orchestrator run {args.name} --run-id {result["run_id"]} --input \'{json.dumps(input_data)}\'')
            
            elif result["status"] == "COMPLETED":
                print("\nWorkflow completed successfully.")
                print("\nFinal state:")
                # Don't print the tools field as it can be very verbose
                shared_state = result["shared_state"].copy()
                if "tools" in shared_state:
                    del shared_state["tools"]
                print(json.dumps(shared_state, indent=2))
            
            elif result["status"] == "FAILED":
                print("\nWorkflow failed.")
                if "error" in result.get("shared_state", {}):
                    print(f"Error: {result['shared_state']['error']}")
        
        except Exception as e:
            print(f"Error running workflow: {str(e)}")
            sys.exit(1)
    
    elif args.command == "step":
        try:
            result = await orchestrator.step_workflow(
                workflow_name=args.name,
                input_data=input_data,
                run_id=args.run_id,
                resume_from=args.step,
                fork=args.fork
            )
            
            print(f"Run ID: {result['run_id']}")
            print(f"Status: {result['status']}")
            
            if result["awaiting_input"]:
                print("\nWorkflow is waiting for input:")
                print(f"  Node ID: {result['awaiting_input']['node_id']}")
                print(f"  Request ID: {result['awaiting_input']['request_id']}")
                print(f"  Prompt: {result['awaiting_input']['prompt']}")
                print(f"  Input Type: {result['awaiting_input']['input_type']}")
                if result['awaiting_input'].get('options'):
                    print(f"  Options: {result['awaiting_input']['options']}")
                
                print("\nTo provide input, use:")
                input_data = {result['awaiting_input']['request_id']: "YOUR_INPUT_HERE"}
                print(f'  orchestrator step {args.name} --run-id {result["run_id"]} --input \'{json.dumps(input_data)}\'')
            
            elif result["continuing"]:
                print("\nWorkflow can continue. Use the same command to execute the next step.")
            
            elif result["status"] == "COMPLETED":
                print("\nWorkflow completed successfully.")
                print("\nFinal state:")
                # Don't print the tools field as it can be very verbose
                shared_state = result["shared_state"].copy()
                if "tools" in shared_state:
                    del shared_state["tools"]
                print(json.dumps(shared_state, indent=2))
            
            elif result["status"] == "FAILED":
                print("\nWorkflow failed.")
                if "error" in result.get("shared_state", {}):
                    print(f"Error: {result['shared_state']['error']}")
        
        except Exception as e:
            print(f"Error stepping workflow: {str(e)}")
            sys.exit(1)
    
    elif args.command == "runs":
        try:
            runs = orchestrator.list_runs(args.name)
            if runs:
                print(f"Runs for workflow '{args.name}':")
                for run_id in runs:
                    run_state = orchestrator.get_run_state(args.name, run_id)
                    status = "Unknown"
                    if run_state and "steps" in run_state and run_state["steps"]:
                        latest_step = run_state["steps"][-1]
                        status = latest_step.get("workflow_status", "Unknown")
                    
                    print(f"  - {run_id} (Status: {status})")
            else:
                print(f"No runs found for workflow '{args.name}'.")
        except Exception as e:
            print(f"Error listing runs: {str(e)}")
            sys.exit(1)
    
    elif args.command == "list-tools":
        tools = orchestrator.list_available_tools()
        print("Available tools:")
        for tool_name in tools:
            tool_details = orchestrator.get_tool_details(tool_name)
            authenticated = "✓" if tool_details.get("authenticated", False) else "✗"
            print(f"  - {tool_name} ({authenticated})")
    
    elif args.command == "tool-details":
        tool_details = orchestrator.get_tool_details(args.name)
        if "error" in tool_details:
            print(f"Error: {tool_details['error']}")
            sys.exit(1)
        
        print(f"Tool: {tool_details['name']}")
        print(f"Description: {tool_details['description']}")
        print(f"Authenticated: {'Yes' if tool_details.get('authenticated', False) else 'No'}")
        print(f"Authentication required: {'Yes' if tool_details.get('auth_required', True) else 'No'}")
        if tool_details.get('connection_id'):
            print(f"Connection ID: {tool_details['connection_id']}")
    
    elif args.command == "authenticate-tool":
        credentials = None
        if args.credentials:
            try:
                credentials = json.loads(args.credentials)
            except json.JSONDecodeError:
                print(f"Error: Invalid JSON credentials: {args.credentials}")
                sys.exit(1)
        
        success = orchestrator.authenticate_tool(args.name, credentials)
        if success:
            print(f"Successfully authenticated with {args.name}")
        else:
            print(f"Failed to authenticate with {args.name}")
            sys.exit(1)
    
    elif args.command == "workflow-tools":
        tools = orchestrator.get_workflow_tools(args.name)
        if tools:
            print(f"Tools used by workflow '{args.name}':")
            for tool_name in tools:
                tool_details = orchestrator.get_tool_details(tool_name)
                authenticated = "✓" if tool_details.get("authenticated", False) else "✗"
                print(f"  - {tool_name} ({authenticated})")
        else:
            print(f"Workflow '{args.name}' doesn't use any tools.")


if __name__ == "__main__":
    asyncio.run(main()) 