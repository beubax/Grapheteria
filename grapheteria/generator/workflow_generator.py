import os
import json
import httpx
from typing import Dict, Any, Tuple, Optional, List
import re
from dotenv import load_dotenv
from grapheteria.generator.tool_manager import ToolManager
from litellm import completion

load_dotenv()

class WorkflowGenerator:
    """
    Generates workflow code and schema using Litellm.
    """
    
    def __init__(self, tool_manager: ToolManager):
        """
        Initialize the workflow generator.
        """
        # Load grapheteria guidelines
        self.grapheteria_guide = self._load_grapheteria_guidelines()
        self.tool_manager = tool_manager
    
    def call_llm(self, prompt: str, llm_model: str) -> str:
        response = completion(
                model=llm_model,
                max_tokens=8000,
                messages=[{"role": "user", "content": prompt}]
            )
        return response.choices[0].message.content
    
    def _load_grapheteria_guidelines(self) -> str:
        """
        Load grapheteria guidelines from file or provide default guidelines.
        
        Returns:
            Guidelines text
        """
        guide_path = os.path.join(os.path.dirname(__file__), "grapheteria_guidelines.md")
        if os.path.exists(guide_path):
            with open(guide_path, "r") as f:
                return f.read()
    
    def _format_tools_documentation(self, tools: List[str]) -> str:
        """
        Format the tools documentation for the prompt.
        
        Args:
            tools: Dictionary of tool objects
            
        Returns:
            Formatted string with tool documentation
        """
        if not tools:
            return ""
        
        if not self.tool_manager:
            raise ValueError("ToolManager not available!")
        
        all_tools = self.tool_manager.get_all_tools()
        authenticated_tools = self.tool_manager.get_authenticated_tools()

        sections = ["## Available Tools"]
        
        for tool_name in tools:
            if tool_name not in all_tools:
                raise ValueError(f"Tool '{tool_name}' is not available")
            
            if tool_name not in authenticated_tools:
                raise ValueError(f"Tool '{tool_name}' is not authenticated")
            
            tool = self.tool_manager.get_tool_info(tool_name)
            
            sections.append(f"### {tool_name.capitalize()} Tool")
            sections.append("Available functions:")
            
            # Add functions with their descriptions
            sections.append(str(tool))
            
            sections.append("")  # Empty line between tools
        
        sections.append("Import the toolset and action from composio_openai import ComposioToolSet, Action. Then initialize the toolset with 'toolset = ComposioToolSet()'")
        sections.append("Execute the function you want to use from the toolset with the format 'toolset.execute_action(action=Action.{function_name}, params=params). Do not await the function, just call it.'")
        
        return "\n".join(sections)
    
    def generate_workflow(self, workflow_id: str, task_description: str, llm_model: str, tools: List[str] = None) -> Tuple[str, Dict[str, Any]]:
        """
        Generate workflow code and schema based on task description.
        
        Args:
            workflow_id: ID of the workflow to generate
            task_description: Description of the task to be accomplished
            llm_model: LLM model to use
            tools: List of tool names to include in the workflow
            
        Returns:
            Tuple of (nodes_code, workflow_schema)
        """
        if not task_description:
            return "", {"nodes": []}
        
        tools_documentation = self._format_tools_documentation(tools or {})
        prompt = f"""
        # Task: Generate a complete workflow for Grapheteria

        ## Workflow ID: {workflow_id}
        
        ## Task Description: 
        {task_description}
        
        ## Grapheteria Guidelines:
        {self.grapheteria_guide}
        
        {tools_documentation}
        
        ## Instructions:
        1. Create a complete nodes.py file with appropriate Node classes needed for this workflow
        2. Create a workflow schema JSON that defines the nodes, edges, and initial state
        3. For any LLM calls, make sure to use litellm using the {llm_model} model and load the api key from the environment variable (make sure to use dot_env).
        4. If tools are available, make sure to use them in your nodes as needed
        5. If the node calls an awaitable function, make sure to use the async keyword in the function definition
        6. Do not use any tools except for the ones provided in the tool documentation
        
        You must respond in the following format:
        
        ```python
        # nodes.py file content here
        ```
        
        ```json
        # Workflow schema JSON here
        ```
        
        The nodes.py file should include all necessary imports and class definitions.
        The workflow schema should define all nodes, edges, starting node, and initial state.
        
        Do not include any explanation, just provide the code and schema as specified.
        """
        
        # Synchronously run the async function
        response = self.call_llm(prompt, llm_model)
        
        # Extract nodes.py content
        nodes_code_match = re.search(r'```python\s*(.*?)\s*```', response, re.DOTALL)
        nodes_code = nodes_code_match.group(1) if nodes_code_match else ""
        
        # Extract JSON schema
        schema_match = re.search(r'```json\s*(.*?)\s*```', response, re.DOTALL)
        schema_str = schema_match.group(1) if schema_match else ""
        
        # Clean up any comments in the JSON
        schema_str = re.sub(r'#.*$', '', schema_str, flags=re.MULTILINE)
        
        try:
            workflow_schema = json.loads(schema_str)
        except json.JSONDecodeError:
            # If there's an error decoding JSON, create a basic schema
            workflow_schema = {
                "nodes": [],
                "edges": [],
                "start": "",
                "initial_state": {}
            }
        
        return nodes_code, workflow_schema
    
    def update_workflow(self, 
                      workflow_id: str, 
                      existing_nodes_code: str,
                      existing_schema: Dict[str, Any],
                      update_description: str,
                      llm_model: str,
                      tools: List[str] = None,
                      ) -> Tuple[str, Dict[str, Any]]:
        """
        Update an existing workflow based on the update description.
        
        Args:
            workflow_id: ID of the workflow to update
            existing_nodes_code: Existing nodes.py content
            existing_schema: Existing workflow schema
            update_description: Description of the updates to be made
            llm_model: LLM model to use
            tools: Dictionary of tool objects to include in the workflow
            
        Returns:
            Tuple of (updated_nodes_code, updated_schema)
        """
        if not update_description:
            return existing_nodes_code, existing_schema
        
        tools_documentation = self._format_tools_documentation(tools or {})
        
        prompt = f"""
        # Task: Update an existing Grapheteria workflow

        ## Workflow ID: {workflow_id}
        
        ## Update Description: 
        {update_description}
        
        ## Existing nodes.py:
        ```python
        {existing_nodes_code}
        ```
        
        ## Existing workflow schema:
        ```json
        {json.dumps(existing_schema, indent=2)}
        ```
        
        ## Grapheteria Guidelines:
        {self.grapheteria_guide}
        
        {tools_documentation}
        
        ## Instructions:
        1. Create a complete nodes.py file with appropriate Node classes needed for this workflow
        2. Create a workflow schema JSON that defines the nodes, edges, and initial state
        3. For any LLM calls, make sure to use litellm using the {llm_model} model and load the api key from the environment variable (make sure to use dot_env).
        4. If tools are available, make sure to use them in your nodes as needed
        
        You must respond in the following format:
        
        ```python
        # Updated nodes.py file content here
        ```
        
        ```json
        # Updated workflow schema JSON here
        ```
        
        The updated nodes.py file should include all necessary imports and class definitions.
        The updated workflow schema should define all nodes, edges, starting node, and initial state.
        
        Do not include any explanation, just provide the updated code and schema as specified.
        """

        # Synchronously run the async function
        response = self.call_llm(prompt, llm_model)
        # Extract updated nodes.py content
        nodes_code_match = re.search(r'```python\s*(.*?)\s*```', response, re.DOTALL)
        updated_nodes_code = nodes_code_match.group(1) if nodes_code_match else existing_nodes_code
        
        # Extract updated JSON schema
        schema_match = re.search(r'```json\s*(.*?)\s*```', response, re.DOTALL)
        schema_str = schema_match.group(1) if schema_match else ""
        
        # Clean up any comments in the JSON
        schema_str = re.sub(r'#.*$', '', schema_str, flags=re.MULTILINE)
        
        try:
            updated_schema = json.loads(schema_str)
        except json.JSONDecodeError:
            # If there's an error decoding JSON, return the existing schema
            updated_schema = existing_schema
        
        return updated_nodes_code, updated_schema 

def generator_create_workflow(
    workflow_id: str,
    task_description: str = None,
    tools: Optional[List[str]] = None,
    tool_manager: Optional[ToolManager] = None,
    workflows_dir: str = ".",
    overwrite: bool = False,
    llm_model: str = "claude-3-5-sonnet-20240620"
):
    """
    Create a new workflow based on the task description.
    Returns a WorkflowEngine instance.
    """
    from grapheteria import WorkflowEngine  # avoid circular import

    # Normalize workflow name
    workflow_id = workflow_id.replace(" ", "_").lower()
    workflow_dir = os.path.join(workflows_dir, workflow_id)

    # Check if workflow already exists
    if os.path.exists(workflow_dir) and not overwrite:
        raise FileExistsError(f"Workflow '{workflow_id}' already exists. Use overwrite=True to replace it.")

    # Create workflow directory
    os.makedirs(workflow_dir, exist_ok=True)

    workflow_generator = WorkflowGenerator(tool_manager)

    # Generate workflow code and schema
    nodes_code, workflow_schema = workflow_generator.generate_workflow(
        workflow_id=workflow_id,
        task_description=task_description,
        tools=tools,
        llm_model=llm_model
    )

    # Save nodes.py
    nodes_path = os.path.join(workflow_dir, "nodes.py")
    with open(nodes_path, "w") as f:
        f.write(nodes_code)

    # Save workflow schema
    schema_path = os.path.join(workflow_dir, "schema.json")
    with open(schema_path, "w") as f:
        json.dump(workflow_schema, f, indent=2)

    #Save tool information
    if tools:
        tool_info = {
            "tools": tools
        }
        tools_path = os.path.join(workflow_dir, "tools.json")
        with open(tools_path, "w") as f:
            json.dump(tool_info, f, indent=2)

    if not workflow_schema.get("nodes"):
        return None
    return WorkflowEngine(workflow_id=workflow_id, workflows_dir=workflows_dir)


def generator_update_workflow(
    workflow_id: str,
    update_description: str,
    tools: Optional[List[str]] = None,
    tool_manager: Optional[ToolManager] = None,
    workflows_dir: str = ".",
    llm_model: str = "claude-3-5-sonnet-20240620"
):
    """
    Update an existing workflow based on the update description.
    Returns a WorkflowEngine instance.
    """
    from grapheteria import WorkflowEngine  # avoid circular import
    import shutil
    from datetime import datetime

    workflow_dir = os.path.join(workflows_dir, workflow_id)

    # Check if workflow exists
    if not os.path.exists(workflow_dir):
        raise FileNotFoundError(f"Workflow '{workflow_id}' not found.")

    # Load existing workflow
    schema_path = os.path.join(workflow_dir, "schema.json")
    nodes_path = os.path.join(workflow_dir, "nodes.py")

    with open(schema_path, "r") as f:
        existing_schema = json.load(f)

    with open(nodes_path, "r") as f:
        existing_nodes_code = f.read()

    workflow_generator = WorkflowGenerator(tool_manager)
    # Generate updated workflow code and schema
    updated_nodes_code, updated_schema = workflow_generator.update_workflow(
        workflow_id=workflow_id,
        existing_nodes_code=existing_nodes_code,
        existing_schema=existing_schema,
        update_description=update_description,
        tools=tools,
        llm_model=llm_model
    )

    # Create backup
    backup_dir = os.path.join(workflow_dir, "backups")
    os.makedirs(backup_dir, exist_ok=True)

    # Get timestamp for backup
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    # Backup nodes.py
    backup_nodes_path = os.path.join(backup_dir, f"nodes_{timestamp}.py")
    shutil.copy2(nodes_path, backup_nodes_path)

    # Backup schema
    backup_schema_path = os.path.join(backup_dir, f"{workflow_id}_{timestamp}.json")
    shutil.copy2(schema_path, backup_schema_path)

    # Save updated nodes.py
    with open(nodes_path, "w") as f:
        f.write(updated_nodes_code)

    # Save updated workflow schema
    with open(schema_path, "w") as f:
        json.dump(updated_schema, f, indent=2)

    #Save tool information
    if tools:
        tool_info = {
            "tools": tools
        }
        tools_path = os.path.join(workflow_dir, "tools.json")
        with open(tools_path, "w") as f:
            json.dump(tool_info, f, indent=2)

    print(f"Updated workflow '{workflow_id}' at {workflow_dir}")
    return WorkflowEngine(workflow_id=workflow_id, workflows_dir=workflows_dir) 