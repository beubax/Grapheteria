
# Tool-Calling with MCP

A comprehensive example demonstrating how to build AI workflows that interact with external tools using Grapheteria and Model Context Protocol (MCP).

## Overview

This example shows how to create a workflow where:
- Users ask research questions
- Claude discovers available tools
- The workflow manages tool selection and execution
- Results are returned to the user with clear explanations
- Users provide feedback on the response quality

## Files

- **mcp_server.py** - Defines tools available through the Model Context Protocol
- **utils.py** - Contains the MCPClient class for tool discovery and execution
- **nodes.py** - Defines the workflow nodes for each step of the process
- **main.py** - Instantiates and runs the workflow with user interaction
- **deploy.py** - FastAPI routes to expose the workflow as an API

## How It Works

The workflow creates a complete tool-using AI assistant:

1. User asks a question
2. System connects to MCP server and discovers available tools
3. Claude examines the question and decides which tools to use
4. System executes selected tools via MCP
5. Claude interprets tool results and provides a final response
6. User provides feedback on the answer

## Setup

```bash
# Install dependencies
pip install grapheteria fastmcp anthropic mcp python-dotenv

# Set your Anthropic API key in the .env file
echo "ANTHROPIC_API_KEY=your-api-key-here" > .env

# Run the example to test functionality 
python main.py

# Or deploy as an API
python deploy.py
```

## Deploying Your MCP Tool-Calling Workflow as an API

The above code creates a FastAPI application with endpoints to manage and interact with the MCP tool-calling workflow. Here's how each endpoint works:

### 1. Create Workflow (`POST /workflows/create`)

This endpoint initializes a new workflow instance with all necessary nodes already connected. It returns a unique `run_id` that you'll use for all subsequent interactions with this workflow.

**Example request:**
```bash
curl -X POST "http://localhost:8000/workflows/create"
```

**Example response:**
```json
{
  "message": "MCP Tool-calling workflow created",
  "run_id": "20241015_123456_789",
  "status": "HEALTHY"
}
```

### 2. Run Through Workflow (`POST /workflows/run/{run_id}`)

This endpoint advances the workflow to the next halt point. If the workflow is waiting for input, you must provide that input. Otherwise, it will execute nodes automatically.

**Example request (without input):**
```bash
curl -X POST "http://localhost:8000/workflows/run/20241015_123456_789"
```

**Example request (with input):**
```bash
curl -X POST "http://localhost:8000/workflows/run/20241015_123456_789" \
  -H "Content-Type: application/json" \
  -d '{"input_value": "What is the capital of France and its population?"}'
```

**Example response (waiting for feedback):**
```json
{
  "status": "WAITING_FOR_INPUT",
  "question": "What is the capital of France and its population?",
  "answer": "The capital of France is Paris with a population of approximately 67 million people.",
  "awaiting_input": {
    "node_id": "feedback",
    "request_id": "feedback",
    "prompt": "Was this answer helpful?",
    "options": ["yes", "no"],
    "input_type": "select"
  }
}
```

### 3. Check Status (`GET /workflows/status/{run_id}`)

This endpoint returns the current status of a workflow without advancing it, showing which node is active and whether it's waiting for input.

**Example request:**
```bash
curl -X GET "http://localhost:8000/workflows/status/20241015_123456_789"
```

**Example response:**
```json
{
  "status": "HEALTHY",
  "current_node": "tool_execution",
  "awaiting_input": null
}
```

### 4. Get Results (`GET /workflows/results/{run_id}`)

This endpoint fetches the current results from the workflow, including the question, answer, and any tool calls that were made.

**Example request:**
```bash
curl -X GET "http://localhost:8000/workflows/results/20241015_123456_789"
```

**Example response:**
```json
{
  "status": "COMPLETED",
  "question": "What is the capital of France and its population?",
  "answer": "The capital of France is Paris with a population of approximately 67 million people.",
  "tool_calls": [
    {
      "id": "tool_1234",
      "name": "get_country_info",
      "input": {"country": "france"}
    }
  ]
}
```

### 5. Delete Workflow (`DELETE /workflows/{run_id}`)

This endpoint removes a workflow instance from memory when you're done with it.

**Example request:**
```bash
curl -X DELETE "http://localhost:8000/workflows/20241015_123456_789"
```

**Example response:**
```json
{
  "message": "Workflow 20241015_123456_789 deleted successfully"
}
```

This API design allows you to:
1. Create multiple independent workflow instances
2. Progress through them at your own pace
3. Handle user input and tool execution seamlessly
4. Monitor workflow status and results
5. Clean up resources when workflows are completed

You can run this FastAPI application with:
```bash
uvicorn deploy:app --reload
```

This will start a local server on port 8000, and you can explore the interactive API documentation at http://localhost:8000/docs. This API makes it easy to integrate tool-using AI capabilities into applications, chatbots, or research tools.

