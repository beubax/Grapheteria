# Grapheteria Task Orchestrator

A lightweight task orchestrator built on top of the Grapheteria state machine framework that enables:

- **LLM-Powered Workflow Generation**: Create workflows from natural language task descriptions
- **Workflow Management**: Create, update, run, and step through workflows
- **State Persistence**: Handle workflow state persistence and resumption
- **Input Handling**: Manage workflow inputs and user interactions
- **Tool Integration**: Integrate with external APIs and services using Composio

## Quick Start

```bash
# Set your Claude API key
export CLAUDE_API_KEY=your_api_key_here

# Create a new workflow
./orchestrator_cli.py create my_workflow "Create a workflow that greets the user and asks for their name"

# Create a workflow with Gmail integration
./orchestrator_cli.py create email_workflow "Create a workflow that reads and processes emails" --tools gmail

# Authenticate with Gmail
./orchestrator_cli.py authenticate-tool gmail

# Run the workflow
./orchestrator_cli.py run email_workflow

# For more detailed examples and documentation:
cat orchestrator/README.md
```

## Directory Structure

- `orchestrator/`: Main package with orchestrator code
  - `generators/`: Workflow generation using LLMs
  - `tools/`: Tool integrations for external services
- `examples/`: Example usage scripts
- `orchestrator_cli.py`: Command-line interface

## Dependencies

- Grapheteria state machine framework
- httpx (for Claude API communication)

## Supported Tools

- Gmail API
- Slack API

More tools can be added by extending the `ComposioTool` base class.

See `orchestrator/requirements.txt` for specific versions. 