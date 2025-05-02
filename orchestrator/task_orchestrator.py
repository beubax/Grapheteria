import os
import json
import shutil
import importlib.util
import sys
from typing import Dict, Any, Optional, List, Callable, Union, Set
import asyncio

from grapheteria import WorkflowEngine, Node, ExecutionState, WorkflowStatus
from grapheteria.utils import FileSystemStorage, path_to_id

from orchestrator.generators.workflow_generator import WorkflowGenerator
from orchestrator.tools.tool_manager import ToolManager


class TaskOrchestrator:
    """
    A lightweight task orchestrator that manages the creation, updating, and execution
    of workflows based on grapheteria state machine.
    """
    
    def __init__(self, 
                workflows_dir: str = "workflows",
                storage_dir: str = "logs",
                api_key: Optional[str] = None):
        """
        Initialize the TaskOrchestrator.
        
        Args:
            workflows_dir: Directory where workflows will be stored
            storage_dir: Directory where workflow execution states will be stored
            api_key: Claude API key (if not provided, will look for CLAUDE_API_KEY env var)
        """
        self.workflows_dir = workflows_dir
        self.storage_dir = storage_dir
        self.storage = FileSystemStorage(base_dir=storage_dir)
        self.api_key = api_key or os.environ.get('CLAUDE_API_KEY')
        
        # Create necessary directories
        os.makedirs(workflows_dir, exist_ok=True)
        os.makedirs(storage_dir, exist_ok=True)
        
        # Initialize tool manager
        self.tool_manager = ToolManager()
        
        # Initialize workflow generator
        self.workflow_generator = WorkflowGenerator(api_key=self.api_key)
        
        # Cache for loaded workflows
        self._workflow_cache = {}
    
    def create_workflow(self, 
                       workflow_name: str, 
                       task_description: str,
                       tools: Optional[List[str]] = None,
                       overwrite: bool = False) -> str:
        """
        Create a new workflow based on the task description.
        
        Args:
            workflow_name: Name of the workflow to create
            task_description: Description of the task to be accomplished
            tools: List of tool names to include in the workflow
            overwrite: Whether to overwrite existing workflow with the same name
            
        Returns:
            Path to the created workflow
        """
        # Normalize workflow name
        workflow_name = workflow_name.replace(" ", "_").lower()
        workflow_dir = os.path.join(self.workflows_dir, workflow_name)
        
        # Check if workflow already exists
        if os.path.exists(workflow_dir) and not overwrite:
            raise FileExistsError(f"Workflow '{workflow_name}' already exists. Use overwrite=True to replace it.")
        
        # Create workflow directory
        os.makedirs(workflow_dir, exist_ok=True)
        
        # Get tool objects for the requested tools
        tool_objects = {}
        if tools:
            tool_objects = {tool_name: self.tool_manager.get_tool(tool_name) for tool_name in tools}
        
        # Generate workflow code and schema
        nodes_code, workflow_schema = self.workflow_generator.generate_workflow(
            workflow_name=workflow_name,
            task_description=task_description,
            tools=tool_objects
        )
        
        # Save nodes.py
        nodes_path = os.path.join(workflow_dir, "nodes.py")
        with open(nodes_path, "w") as f:
            f.write(nodes_code)
        
        # Save workflow schema
        schema_path = os.path.join(workflow_dir, f"{workflow_name}.json")
        with open(schema_path, "w") as f:
            json.dump(workflow_schema, f, indent=2)
        
        # Save tool information
        if tools:
            tool_info = {
                "tools": tools
            }
            tools_path = os.path.join(workflow_dir, "tools.json")
            with open(tools_path, "w") as f:
                json.dump(tool_info, f, indent=2)
        
        print(f"Created workflow '{workflow_name}' at {workflow_dir}")
        return workflow_dir
    
    def update_workflow(self, 
                      workflow_name: str, 
                      update_description: str,
                      tools: Optional[List[str]] = None) -> str:
        """
        Update an existing workflow based on the update description.
        
        Args:
            workflow_name: Name of the workflow to update
            update_description: Description of the updates to be made
            tools: List of tool names to include in the workflow (will be merged with existing tools)
            
        Returns:
            Path to the updated workflow
        """
        workflow_dir = os.path.join(self.workflows_dir, workflow_name)
        
        # Check if workflow exists
        if not os.path.exists(workflow_dir):
            raise FileNotFoundError(f"Workflow '{workflow_name}' not found.")
        
        # Load existing workflow
        schema_path = os.path.join(workflow_dir, f"{workflow_name}.json")
        nodes_path = os.path.join(workflow_dir, "nodes.py")
        
        with open(schema_path, "r") as f:
            existing_schema = json.load(f)
        
        with open(nodes_path, "r") as f:
            existing_nodes_code = f.read()
        
        # Load existing tools
        existing_tools = []
        tools_path = os.path.join(workflow_dir, "tools.json")
        if os.path.exists(tools_path):
            with open(tools_path, "r") as f:
                tool_info = json.load(f)
                existing_tools = tool_info.get("tools", [])
        
        # Merge existing and new tools
        all_tools = set(existing_tools)
        if tools:
            all_tools.update(tools)
        
        # Get tool objects for all tools
        tool_objects = {}
        if all_tools:
            tool_objects = {tool_name: self.tool_manager.get_tool(tool_name) for tool_name in all_tools}
        
        # Generate updated workflow code and schema
        updated_nodes_code, updated_schema = self.workflow_generator.update_workflow(
            workflow_name=workflow_name,
            existing_nodes_code=existing_nodes_code,
            existing_schema=existing_schema,
            update_description=update_description,
            tools=tool_objects
        )
        
        # Create backup
        backup_dir = os.path.join(workflow_dir, "backups")
        os.makedirs(backup_dir, exist_ok=True)
        
        # Get timestamp for backup
        from datetime import datetime
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Backup nodes.py
        backup_nodes_path = os.path.join(backup_dir, f"nodes_{timestamp}.py")
        shutil.copy2(nodes_path, backup_nodes_path)
        
        # Backup schema
        backup_schema_path = os.path.join(backup_dir, f"{workflow_name}_{timestamp}.json")
        shutil.copy2(schema_path, backup_schema_path)
        
        # Backup tools if they exist
        if os.path.exists(tools_path):
            backup_tools_path = os.path.join(backup_dir, f"tools_{timestamp}.json")
            shutil.copy2(tools_path, backup_tools_path)
        
        # Save updated nodes.py
        with open(nodes_path, "w") as f:
            f.write(updated_nodes_code)
        
        # Save updated workflow schema
        with open(schema_path, "w") as f:
            json.dump(updated_schema, f, indent=2)
        
        # Save updated tool information
        if all_tools:
            tool_info = {
                "tools": list(all_tools)
            }
            with open(tools_path, "w") as f:
                json.dump(tool_info, f, indent=2)
        
        # Clear cache for this workflow
        if workflow_name in self._workflow_cache:
            del self._workflow_cache[workflow_name]
        
        print(f"Updated workflow '{workflow_name}' at {workflow_dir}")
        return workflow_dir
    
    def _load_workflow_nodes(self, workflow_name: str) -> Dict[str, type]:
        """
        Dynamically load the workflow nodes module.
        
        Args:
            workflow_name: Name of the workflow
            
        Returns:
            Dictionary of node classes from the module
        """
        if workflow_name in self._workflow_cache:
            return self._workflow_cache[workflow_name]
        
        nodes_path = os.path.join(self.workflows_dir, workflow_name, "nodes.py")
        
        # Load the module
        spec = importlib.util.spec_from_file_location(f"workflow_{workflow_name}_nodes", nodes_path)
        nodes_module = importlib.util.module_from_spec(spec)
        sys.modules[f"workflow_{workflow_name}_nodes"] = nodes_module
        spec.loader.exec_module(nodes_module)
        
        # Get all Node subclasses from the module
        node_classes = {}
        for name in dir(nodes_module):
            obj = getattr(nodes_module, name)
            if isinstance(obj, type) and issubclass(obj, Node) and obj != Node:
                node_classes[name] = obj
        
        # Cache the result
        self._workflow_cache[workflow_name] = node_classes
        
        return node_classes
    
    def get_workflow_engine(self, 
                         workflow_name: str, 
                         run_id: Optional[str] = None,
                         resume_from: Optional[int] = None,
                         fork: bool = False) -> WorkflowEngine:
        """
        Get a workflow engine instance for the specified workflow.
        
        Args:
            workflow_name: Name of the workflow
            run_id: ID of an existing run to resume (optional)
            resume_from: Step index to resume from (optional)
            fork: Whether to fork the workflow run (optional)
            
        Returns:
            WorkflowEngine instance
        """
        workflow_path = os.path.join(self.workflows_dir, workflow_name, f"{workflow_name}.json")
        
        # Load tool information
        tools_path = os.path.join(self.workflows_dir, workflow_name, "tools.json")
        tool_objects = {}
        if os.path.exists(tools_path):
            with open(tools_path, "r") as f:
                tool_info = json.load(f)
                tools = tool_info.get("tools", [])
                tool_objects = {tool_name: self.tool_manager.get_tool(tool_name) for tool_name in tools}
        
        # Create initial state with tools
        initial_shared_state = {"tools": tool_objects} if tool_objects else {}
        
        # Create and return the workflow engine
        engine = WorkflowEngine(
            workflow_path=workflow_path,
            run_id=run_id,
            resume_from=resume_from,
            fork=fork,
            storage_backend=self.storage,
            initial_shared_state=initial_shared_state
        )
        
        return engine
    
    async def run_workflow(self, 
                     workflow_name: str, 
                     input_data: Optional[Dict[str, Any]] = None,
                     run_id: Optional[str] = None,
                     resume_from: Optional[int] = None,
                     fork: bool = False) -> Dict[str, Any]:
        """
        Run a workflow to completion or until it requires input.
        
        Args:
            workflow_name: Name of the workflow to run
            input_data: Input data for the workflow
            run_id: ID of an existing run to resume (optional)
            resume_from: Step index to resume from (optional)
            fork: Whether to fork the workflow run (optional)
            
        Returns:
            Final workflow state
        """
        engine = self.get_workflow_engine(workflow_name, run_id, resume_from, fork)
        
        # Run the workflow
        continuing = await engine.run(input_data)
        
        # Return the final state
        return {
            "run_id": engine.run_id,
            "workflow_id": engine.workflow_id,
            "status": engine.execution_state.workflow_status.name,
            "shared_state": engine.execution_state.shared,
            "awaiting_input": engine.execution_state.awaiting_input,
            "continuing": continuing
        }
    
    async def step_workflow(self,
                     workflow_name: str,
                     input_data: Optional[Dict[str, Any]] = None,
                     run_id: Optional[str] = None,
                     resume_from: Optional[int] = None,
                     fork: bool = False) -> Dict[str, Any]:
        """
        Execute a single step of a workflow.
        
        Args:
            workflow_name: Name of the workflow to step
            input_data: Input data for the workflow
            run_id: ID of an existing run to resume (optional)
            resume_from: Step index to resume from (optional)
            fork: Whether to fork the workflow run (optional)
            
        Returns:
            Current workflow state
        """
        engine = self.get_workflow_engine(workflow_name, run_id, resume_from, fork)
        
        # Execute a single step
        continuing = await engine.step(input_data)
        
        # Return the current state
        return {
            "run_id": engine.run_id,
            "workflow_id": engine.workflow_id,
            "status": engine.execution_state.workflow_status.name,
            "shared_state": engine.execution_state.shared,
            "awaiting_input": engine.execution_state.awaiting_input,
            "continuing": continuing
        }
    
    def list_workflows(self) -> List[str]:
        """
        List all available workflows.
        
        Returns:
            List of workflow names
        """
        if not os.path.exists(self.workflows_dir):
            return []
        
        return [d for d in os.listdir(self.workflows_dir) 
                if os.path.isdir(os.path.join(self.workflows_dir, d))
                and os.path.exists(os.path.join(self.workflows_dir, d, f"{d}.json"))]
    
    def list_runs(self, workflow_name: str) -> List[str]:
        """
        List all runs for a specific workflow.
        
        Args:
            workflow_name: Name of the workflow
            
        Returns:
            List of run IDs
        """
        workflow_id = path_to_id(os.path.join(self.workflows_dir, workflow_name, f"{workflow_name}.json"))
        return self.storage.list_runs(workflow_id)
    
    def get_run_state(self, workflow_name: str, run_id: str) -> Optional[Dict[str, Any]]:
        """
        Get the state of a specific workflow run.
        
        Args:
            workflow_name: Name of the workflow
            run_id: ID of the run
            
        Returns:
            Run state dict if found, None otherwise
        """
        workflow_id = path_to_id(os.path.join(self.workflows_dir, workflow_name, f"{workflow_name}.json"))
        return self.storage.load_state(workflow_id, run_id)
    
    def list_available_tools(self) -> List[str]:
        """
        List all available tools that can be used in workflows.
        
        Returns:
            List of tool names
        """
        return self.tool_manager.list_available_tools()
    
    def get_tool_details(self, tool_name: str) -> Dict[str, Any]:
        """
        Get details about a specific tool.
        
        Args:
            tool_name: Name of the tool
            
        Returns:
            Dictionary with tool details
        """
        return self.tool_manager.get_tool_details(tool_name)
    
    def authenticate_tool(self, tool_name: str, credentials: Dict[str, Any] = None) -> bool:
        """
        Authenticate with a specific tool.
        
        Args:
            tool_name: Name of the tool to authenticate with
            credentials: Authentication credentials (if required)
            
        Returns:
            True if authentication was successful, False otherwise
        """
        return self.tool_manager.authenticate_tool(tool_name, credentials)
    
    def get_workflow_tools(self, workflow_name: str) -> List[str]:
        """
        Get the tools used by a specific workflow.
        
        Args:
            workflow_name: Name of the workflow
            
        Returns:
            List of tool names used by the workflow
        """
        tools_path = os.path.join(self.workflows_dir, workflow_name, "tools.json")
        if not os.path.exists(tools_path):
            return []
        
        with open(tools_path, "r") as f:
            tool_info = json.load(f)
            return tool_info.get("tools", []) 