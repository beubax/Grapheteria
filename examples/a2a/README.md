
# Content Generation with A2A Protocol

A powerful example demonstrating how to deploy a Grapheteria workflow using Google's Agent-to-Agent (A2A) protocol, creating a content generation agent that supports multi-turn conversations.

## Overview

This example shows how to:
- Deploy a workflow as an A2A-compatible agent
- Enable streaming, push notifications, and persistent conversations
- Create a content generation workflow with human review

## File Structure

- **common/** - Directory containing Google's A2A protocol implementation (unmodified from [Google's A2A repository](https://github.com/google-ai/agent-to-agent))
- **client.py** - CLI tool for testing A2A agents locally (from Google's repository)
- **flow.py** - Defines the content generation workflow nodes and their connections
- **main.py** - Server startup code and agent capability declaration (agent card)
- **task_manager.py** - Bridges Grapheteria's workflow engine with A2A's task management
- **utils.py** - Helper functions including LLM integration
- **workflow.json** - Workflow schema that can be visualized/edited in the UI

## Key Components

```15:28:examples/a2a/flow.py
class GenerateContentNode(Node):
    async def prepare(self, shared, request_input):
        topic = await request_input(
            prompt="What topic would you like an article about?",
            input_type="text",
            request_id="generate_content"
        )
        shared["topic"] = topic 
        return topic

    def execute(self, topic):
        prompt = f"Write an informative article about {topic}"
        article = call_llm(prompt)
        return article
```

The workflow handles the full content creation lifecycle - from topic selection to generation, human review, and optional revision based on feedback.

```23:42:examples/a2a/main.py
capabilities = AgentCapabilities(streaming=True, pushNotifications=True)
skill = AgentSkill(
    id="generate_content",
    name="Content Generation",
    description="Generates content for a given topic",
    tags=["content generation", "content writing"],
    examples=["Write an informative article about {topic}"],
)
```

## Supported Features

This implementation supports all A2A protocol features:
- ⚡ **Streaming responses** - See content generation in real-time
- 🔔 **Push notifications** - Get notified when tasks complete
- 💬 **Multi-turn conversations** - Review and revise content iteratively
- 🧠 **Conversation memory** - Agent remembers previous interactions in a session

## Running the Example

1. Start the server:
```
uv run examples/a2a/main.py
```

2. In a separate terminal, run the client:
```
uv run examples/a2a/client.py
```

## Example Interaction

```
======= Agent Card ========
{"name":"Content Generation Agent","description":"Helps with content generation",...}
=========  starting a new task ======== 

What do you want to send to the agent? (:q or quit to exit)
> Write one line about space

[Agent generates article about space...]

Do you approve this content?
> approve

[Final article delivered]
stream event => {"jsonrpc":"2.0",...,"status":{"state":"completed"}}
```

This implementation demonstrates how Grapheteria workflows can be easily deployed as standards-compliant A2A agents, enabling powerful, interactive AI applications with human oversight.
