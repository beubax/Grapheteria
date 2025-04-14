
# Content Creation with Human Approval

A simple example demonstrating how to build a human-in-the-loop AI content generation workflow using Grapheteria.

## Overview

This example shows how to create a workflow where:
- Users specify a topic
- AI generates content
- Humans review and approve/reject
- Content is published or revised based on feedback

## Files

- **utils.py** - Contains the OpenAI API integration for text generation
- **nodes.py** - Defines the workflow nodes
- **main.py** - Instantiates and runs the workflow with user interaction
- **workflow.json** - Workflow schema in JSON for UI
- **deploy.py** - Sample FastAPI routes to deploy this workflow

## How It Works

The workflow creates a feedback loop between AI and humans:

1. User provides a topic
2. OpenAI generates an article
3. User reviews and decides to approve or reject
4. If approved, content is published
5. If rejected, user provides feedback and AI revises

## Setup

```bash
# Install dependencies
pip install grapheteria openai

# Set your OpenAI API key in the .env file

# Run the example to test functionality 
python main.py
```

## Using the API

With the FastAPI application in `deploy.py`, you can interact with your content creation workflow through HTTP requests.

### Example workflow interaction:

1. Create a new workflow:
   ```bash
   curl -X POST "{api_route}/workflows/create"
   ```
   Response:
   ```json
   {
     "message": "Content workflow created",
     "run_id": "20230815_123456_789",
     "status": "HEALTHY"
   }
   ```

2. Start the workflow (this will ask for a topic):
   ```bash
   curl -X POST "{api_route}/workflows/run/20230815_123456_789"
   ```
   Response:
   ```json
   {
     "status": "WAITING_FOR_INPUT",
     "awaiting_input": {
       "node_id": "topic_request",
       "prompt": "What topic would you like an article about?",
       "input_type": "text"
     }
   }
   ```

3. Provide the topic:
   ```bash
   curl -X POST "{api_route}/workflows/run/20230815_123456_789" \
     -H "Content-Type: application/json" \
     -d '{"input_value": "artificial intelligence"}'
   ```
   Response (workflow moves to content generation and then asks for feedback):
   ```json
   {
     "status": "WAITING_FOR_INPUT",
     "article": "Generated article.....",
     "awaiting_input": {
       "node_id": "human_review",
       "prompt": "Do you approve this content?",
       "options": ["approve", "reject"],
       "input_type": "select"
     }

   }
   ```

4. Provide approval/rejection:
   ```bash
   curl -X POST "{api_route}/workflows/20230815_123456_789/step" \
     -H "Content-Type: application/json" \
     -d '{"input_value": "approve"}'
   ```
   Response:
   ```json
   {
     "status": "COMPLETED",
     "article": "This is an article about artificial intelligence..."
   }
   ```

This API makes it easy to integrate the human-in-the-loop workflow into web applications, chatbots, or other systems that need AI-generated content with human oversight.



