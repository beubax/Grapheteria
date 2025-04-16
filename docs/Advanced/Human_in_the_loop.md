---
layout: default
title: "Human-in-the-Loop"
parent: "Advanced"
nav_order: 3
---

# Human-in-the-Loop: Halting and Resuming Workflows

## The Need for Human Input

In agentic workflows, we often need humans to validate, correct, or provide data that machines can't determine. Like asking your GPS if you should take that questionable shortcut through what appears to be someone's backyard - sometimes human judgment is irreplaceable.

Our state machine provides a built-in mechanism for pausing execution, collecting human input, and seamlessly resuming - whether immediately or days later.

## How It Works: Futures and States

The system uses Python's `asyncio.Future` objects to implement halting. When a node requests input:

```python
user_name = await request_input(prompt="What's your name?")
print(f"Hello, {user_name}!")
```

Behind the scenes:
1. The workflow status changes to `WAITING_FOR_INPUT`
2. The current state is saved
3. A future is created and awaited, pausing execution
4. When input arrives, the future resolves and execution continues

## Resumption Behavior

There are two ways execution can resume after requesting input:

### Same-Process Resumption
If input is provided while the original process is still running (meaning the workflow hasn't been stopped and resumed with a new WorkflowEngine instance):

```python
# In your workflow node
data = await request_input(prompt="Enter data:")
process_data(data)  # Continues from exactly here
```

### Cross-Process Resumption
If the workflow is stopped and later restarted:

```python
# First execution
data = await request_input(prompt="Enter data:")  # Halts here

# Days later, workflow engine restarts
data = await request_input(prompt="Enter data:")  # Re-executes this line
process_data(data)  # Then continues
```

⚠️ **Important**: Code before the `await` will execute twice in cross-process resumption. Avoid side effects before await points:
{: .highlight}

```python
# BAD: Side effect before await
send_notification()  # Will run twice if resumed cross-process
data = await request_input(prompt="Enter data:")

# GOOD: Side effect after await  
data = await request_input(prompt="Enter data:")
send_notification()  # Will only run once
```

## Request Input Parameters

The `request_input` function accepts these parameters:

```python
async def request_input(prompt=None, options=None, input_type="text", request_id=None):
```

- `prompt`: Text shown to the user (e.g., "What's your name?")
- `options`: Available choices for selection inputs
- `input_type`: Format of input ("text", "select", etc.)
- `request_id`: Custom identifier for this specific input request

All of these are optional and do not necessarily have to be used.

The `request_id` is critical when the same node has multiple input requests:

```python
name = await request_input(prompt="Name?", request_id="name_field")
age = await request_input(prompt="Age?", request_id="age_field")
```

Without unique `request_id's`, any input provided with just a `node_id` would satisfy both requests!

## Providing Input Data

To resume a workflow, provide input as a dictionary to either the `step()` or `run()` methods of the workflow engine:

```python
# For inputs with default node IDs
input_data = {
    "TextInputNode_12345": "User's response"
}

# For inputs with custom request IDs
input_data = {
    "name_field": "Alice",
    "age_field": 30
}

# Complex input data is also supported
input_data = {
    "form_response": {
        "name": "Bob",
        "preferences": ["pizza", "hiking"]
    }
}

# Resume workflow with inputs
await workflow.run(input_data)
```

> The key in the dictionary must match either the node ID or the custom request ID. The respective value is the actual input data you wish to provide to the node.
{: .note}


### How do we find out when to provide input?

`workflow.run()` continues running until it reaches a halt point. When it stops, we need to figure out why - did it finish, fail, or is it just waiting for your input?

#### Method 1: Check the return value and status (great for terminal use)
```python
# Running workflow execution loop
while True:
    # Run the workflow
    await workflow.run()
    
    # Workflow stopped - check if it needs input
    if workflow.execution_state.awaiting_input:
        # Workflow is stuck until we provide input
        request = workflow.execution_state.awaiting_input
        
        print(f"Input needed: {request['prompt']}")
        if request['input_type'] == 'select':
            print(f"Options: {request['options']}")
        
        # Collect input and feed it to the workflow
        user_answer = input("Your response: ")
        await workflow.step({request['request_id']: user_answer})
        continue

    # Workflow completed or failed
    break
```

#### Method 2: Server-based detection (cleaner approach)

Running your workflow in tandem with a [server](Deployment) lets you run your workflow as a service, checking its status and feeding it input whenever needed - no need to babysit the process!

```python
from fastapi import FastAPI
import asyncio

app = FastAPI()
workflow = None

@app.post("/start-workflow")
async def start_workflow():
    global workflow
    workflow = WorkflowEngine(...)
    asyncio.create_task(workflow.run())
    return {"status": "started"}

@app.get("/workflow-status")
async def get_status():
    if workflow.execution_state.awaiting_input:
        return {
            "status": "waiting_for_input",
            "request": workflow.execution_state.awaiting_input
        }
    return {"status": workflow.execution_state.workflow_status.name}

@app.post("/provide-input")
async def provide_input(input_data: dict):
    request_id = workflow.execution_state.awaiting_input["request_id"]
    await workflow.step({request_id: input_data["value"]})
    return {"status": "input_provided"}
```

Grapheteria comes with a built-in UI that uses this server approach, making it super easy to visualize your workflow, debug it, and provide input when needed. Just run `grapheteria` in your terminal to launch the UI and interact with your workflows visually instead of juggling print statements and keyboard inputs!

## Complete Example
For an end-to-end example of a human-in-the-loop workflow, check out our [Content Creation Example](../Cookbook/Human_in_the_loop) in the cookbook. It demonstrates a complete implementation with AI-generated content that requires human approval before publication.