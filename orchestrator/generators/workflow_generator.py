import os
import json
import httpx
from typing import Dict, Any, Tuple, Optional, List
import re


class WorkflowGenerator:
    """
    Generates workflow code and schema using Claude 3.7 Sonnet.
    """
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize the workflow generator.
        
        Args:
            api_key: Claude API key (if not provided, will look for CLAUDE_API_KEY env var)
        """
        self.api_key = api_key or os.environ.get('CLAUDE_API_KEY')
        if not self.api_key:
            raise ValueError("Claude API key not provided and CLAUDE_API_KEY environment variable not set")
        
        # Claude API configurations
        self.api_url = "https://api.anthropic.com/v1/messages"
        self.model = "claude-3-sonnet-20240229"
        self.max_tokens = 4000
        
        # Load grapheteria guidelines
        self.grapheteria_guide = self._load_grapheteria_guidelines()
    
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
        else:
            # Provide default guidelines if file not found
            return """
            # Grapheteria Guidelines
            
            Grapheteria is a framework for building state machine-based workflows.
            
            ## Core Components:
            
            1. **Node**: Base class for all workflow nodes. Each node should:
               - Define `prepare`, `execute`, and `cleanup` methods
               - Handle any errors properly
               - Return appropriate values to be used by next nodes
            
            2. **Edge**: Connects nodes together, optionally with conditions
            
            3. **WorkflowEngine**: Runs the workflow
            
            ## Creating Nodes:
            
            Nodes must inherit from `Node` and implement:
            
            ```python
            def prepare(self, shared, request_input):
                # Prepare data for execution
                pass
                
            def execute(self, prepared_data):
                # Execute node logic
                pass
                
            def cleanup(self, shared, prepared_data, execution_result):
                # Store results in shared state
                shared["some_key"] = execution_result
                pass
            ```
            
            ## Creating Workflows:
            
            Workflows are defined through JSON or code:
            
            ```python
            # Construct nodes
            start_node = StartNode(id="start")
            process_node = ProcessNode(id="process")
            end_node = EndNode(id="end")
            
            # Connect nodes 
            start_node > process_node > end_node
            
            # Conditional edges
            process_node - "shared['status'] == 'success'" > success_node
            process_node - "shared['status'] == 'failure'" > failure_node
            ```
            
            ## JSON Schema format:
            
            ```json
            {
              "nodes": [
                {"id": "start", "class": "StartNode", "config": {}},
                {"id": "process", "class": "ProcessNode", "config": {}},
                {"id": "end", "class": "EndNode", "config": {}}
              ],
              "edges": [
                {"from": "start", "to": "process", "condition": ""},
                {"from": "process", "to": "end", "condition": ""}
              ],
              "start": "start",
              "initial_state": {}
            }
            ```
            """
    
    def _format_tools_documentation(self, tools: Dict[str, Any]) -> str:
        """
        Format the tools documentation for the prompt.
        
        Args:
            tools: Dictionary of tool objects
            
        Returns:
            Formatted string with tool documentation
        """
        if not tools:
            return ""
        
        sections = ["## Available Tools"]
        
        for tool_name, tool in tools.items():
            sections.append(f"### {tool_name.capitalize()} Tool")
            sections.append(f"Description: {tool.description}")
            sections.append("Available functions:")
            
            # Add functions with their descriptions
            for func_name, composio_name in tool.functions.items():
                sections.append(f"- `{func_name}`: {composio_name}")
            
            sections.append("")  # Empty line between tools
        
        sections.append("Access tools from `shared['tools']['{tool_name}']`, e.g., `shared['tools']['gmail'].send_email(params)`")
        
        return "\n".join(sections)
    
    async def _query_claude(self, prompt: str) -> str:
        """
        Query Claude with the given prompt.
        
        Args:
            prompt: The prompt to send to Claude
            
        Returns:
            Claude's response text
        """
        headers = {
            "anthropic-version": "2023-06-01",
            "x-api-key": self.api_key,
            "content-type": "application/json"
        }
        
        data = {
            "model": self.model,
            "max_tokens": self.max_tokens,
            "messages": [
                {"role": "user", "content": prompt}
            ]
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.post(self.api_url, json=data, headers=headers)
            response.raise_for_status()
            result = response.json()
            return result["content"][0]["text"]
    
    def generate_workflow(self, workflow_name: str, task_description: str, tools: Dict[str, Any] = None) -> Tuple[str, Dict[str, Any]]:
        """
        Generate workflow code and schema based on task description.
        
        Args:
            workflow_name: Name of the workflow to generate
            task_description: Description of the task to be accomplished
            tools: Dictionary of tool objects to include in the workflow
            
        Returns:
            Tuple of (nodes_code, workflow_schema)
        """
        tools_documentation = self._format_tools_documentation(tools or {})
        
        prompt = f"""
        # Task: Generate a complete workflow for Grapheteria

        ## Workflow Name: {workflow_name}
        
        ## Task Description: 
        {task_description}
        
        ## Grapheteria Guidelines:
        {self.grapheteria_guide}
        
        {tools_documentation}
        
        ## Instructions:
        1. Create a complete nodes.py file with appropriate Node classes needed for this workflow
        2. Create a workflow schema JSON that defines the nodes, edges, and initial state
        3. If tools are available, make sure to use them in your nodes as needed
        4. When accessing tools, use them from the shared state: `shared['tools']['{tool_name}'].function_name(params)`
        5. Tools may need asynchronous calls, use `await` when calling tool functions
        
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
        import asyncio
        response = asyncio.run(self._query_claude(prompt))
        
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
                      workflow_name: str, 
                      existing_nodes_code: str,
                      existing_schema: Dict[str, Any],
                      update_description: str,
                      tools: Dict[str, Any] = None) -> Tuple[str, Dict[str, Any]]:
        """
        Update an existing workflow based on the update description.
        
        Args:
            workflow_name: Name of the workflow to update
            existing_nodes_code: Existing nodes.py content
            existing_schema: Existing workflow schema
            update_description: Description of the updates to be made
            tools: Dictionary of tool objects to include in the workflow
            
        Returns:
            Tuple of (updated_nodes_code, updated_schema)
        """
        tools_documentation = self._format_tools_documentation(tools or {})
        
        prompt = f"""
        # Task: Update an existing Grapheteria workflow

        ## Workflow Name: {workflow_name}
        
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
        1. Update the nodes.py file according to the update description
        2. Update the workflow schema accordingly
        3. Make sure to preserve existing functionality unless explicitly changed
        4. If tools are available, make sure to use them in your nodes as needed
        5. When accessing tools, use them from the shared state: `shared['tools']['{tool_name}'].function_name(params)`
        6. Tools may need asynchronous calls, use `await` when calling tool functions
        
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
        import asyncio
        response = asyncio.run(self._query_claude(prompt))
        
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