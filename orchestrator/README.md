# Grapheteria Task Orchestrator

A lightweight task orchestrator built on top of Grapheteria state machine framework. The orchestrator allows you to:

1. Generate workflows from natural language task descriptions
2. Update existing workflows based on change requests
3. Run and step through workflows
4. Handle workflow state persistence and resumption
5. Integrate with external tools using Composio

## Installation

Ensure you have Grapheteria installed, then install the required dependencies:

```bash
pip install httpx
```

## Usage

### Command Line Interface

The orchestrator provides a command-line interface for common operations:

```bash
# Create a new workflow
./orchestrator_cli.py create workflow_name "Task description goes here"

# Create a workflow with tools
./orchestrator_cli.py create workflow_name "Task description" --tools gmail,slack

# Update an existing workflow
./orchestrator_cli.py update workflow_name "Updates to make to the workflow"

# Add tools to an existing workflow
./orchestrator_cli.py update workflow_name "Updates" --tools gmail

# List available workflows
./orchestrator_cli.py list

# Run a workflow
./orchestrator_cli.py run workflow_name

# Step through a workflow
./orchestrator_cli.py step workflow_name

# List runs for a workflow
./orchestrator_cli.py runs workflow_name

# List available tools
./orchestrator_cli.py list-tools

# Get details about a specific tool
./orchestrator_cli.py tool-details gmail

# Authenticate with a tool
./orchestrator_cli.py authenticate-tool gmail

# List tools used by a workflow
./orchestrator_cli.py workflow-tools workflow_name
```

### Python API

#### Creating a Workflow

```python
from orchestrator import TaskOrchestrator
import asyncio

# Initialize the orchestrator
orchestrator = TaskOrchestrator()

# Create a new workflow
workflow_dir = orchestrator.create_workflow(
    workflow_name="data_processing",
    task_description="Create a workflow that reads a CSV file, processes the data, and generates a report",
)

# Create a workflow with tools
workflow_dir = orchestrator.create_workflow(
    workflow_name="email_processor",
    task_description="Create a workflow that reads emails and responds to important ones",
    tools=["gmail"]
)
```

#### Running a Workflow

```python
async def run_workflow():
    # Run the workflow
    result = await orchestrator.run_workflow(workflow_name="data_processing")
    
    # If input is required
    if result["awaiting_input"]:
        request_id = result["awaiting_input"]["request_id"]
        input_data = {request_id: "user input goes here"}
        
        # Continue with input
        result = await orchestrator.run_workflow(
            workflow_name="data_processing",
            run_id=result["run_id"],
            input_data=input_data
        )

# Run the async function
asyncio.run(run_workflow())
```

#### Stepping Through a Workflow

```python
async def step_workflow():
    # Step through the workflow
    result = await orchestrator.step_workflow(workflow_name="data_processing")
    
    # If step completed but more steps are available
    if result["continuing"]:
        # Run the next step
        result = await orchestrator.step_workflow(
            workflow_name="data_processing",
            run_id=result["run_id"]
        )

# Run the async function
asyncio.run(step_workflow())
```

#### Working with Tools

```python
# List available tools
tools = orchestrator.list_available_tools()

# Get details about a specific tool
tool_details = orchestrator.get_tool_details("gmail")

# Authenticate with a tool
success = orchestrator.authenticate_tool("gmail")

# Get tools used by a workflow
workflow_tools = orchestrator.get_workflow_tools("email_processor")
```

## Configuration

The TaskOrchestrator accepts several configuration parameters:

```python
orchestrator = TaskOrchestrator(
    workflows_dir="workflows",  # Directory to store workflows
    storage_dir="logs",         # Directory to store execution logs
    api_key="your_claude_api_key"  # Claude API key (can also use CLAUDE_API_KEY env var)
)
```

## Workflow Structure

Each workflow is stored in its own directory with the following structure:

```
workflows/
  workflow_name/
    nodes.py          # Contains the Node classes for the workflow
    workflow_name.json # Workflow schema defining nodes and edges
    tools.json        # Information about tools used by the workflow
    backups/          # Backup directory for previous versions
```

## LLM-based Workflow Generation

The orchestrator uses Claude 3.7 Sonnet to generate workflows based on natural language descriptions. It creates:

1. Custom Node classes tailored to the task
2. A workflow schema that connects the nodes
3. Proper error handling and state management
4. Integration with external tools when specified

## Tool Integration

The orchestrator supports tool integration via Composio:

1. **Built-in Tools**:
   - Gmail: Access to the Gmail API
   - Slack: Access to the Slack API

2. **Using Tools in Workflows**:
   Tools are passed to the workflow nodes and can be accessed via `shared['tools']` in the node methods:

   ```python
   async def execute(self, prepared_data):
       gmail_tool = shared['tools']['gmail']
       result = await gmail_tool.send_email({
           "recipient_email": "user@example.com",
           "subject": "Test email",
           "body": "This is a test email"
       })
       return result
   ```

3. **Extending with New Tools**:
   Create a new tool class that inherits from `ComposioTool` and register it with the `ToolManager`:

   ```python
   from orchestrator.tools import ComposioTool, ToolManager
   
   class MyTool(ComposioTool):
       # Implementation...
   
   # Register the tool
   tool_manager = ToolManager()
   tool_manager.register_tool("my_tool", MyTool())
   ```

## Examples

See the `examples/` directory for more detailed examples of using the orchestrator.

## Extending the Orchestrator

You can extend the orchestrator by:

1. Adding new generator models
2. Creating custom Node base classes
3. Implementing specialized storage backends
4. Building visualization tools for workflows
5. Adding new tool integrations

## License

Same as the Grapheteria framework. 