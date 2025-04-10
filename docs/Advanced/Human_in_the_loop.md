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

> Same process resumption is quite tricky to get right. An await operation on the `asyncio.Future` object blocks python's event loop, causing your workflow to become seemingly unresponsive. In reality, it is currently awaiting and this is intended behavior. To design a seamless system, use your workflow in tandem with a [server](Deployment). This way python switches between coroutines and you can provide inputs with ease.
{: .note}

## Resumption Behavior

There are two ways execution can resume after requesting input:

### Same-Process Resumption
If input arrives while the original process is still running:

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

The `request_id` is critical when a node has multiple input requests:

```python
name = await request_input(prompt="Name?", request_id="name_field")
age = await request_input(prompt="Age?", request_id="age_field")
```

Without unique `request_id`s, the same input would satisfy both requests!

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
await workflow.step(input_data)
```

> The key in the dictionary must match either the node ID or the custom request ID. The respective value is the actual input data you wish to provide to the node.
{: .note}

## Input Consumption Behavior

When a workflow is halted:

1. You must call `workflow.step()` or `workflow.run()` with input data to resume
2. Inputs are consumed when used and won't persist for future requests
3. If inputs are provided for the wrong halted node, the workflow remains halted
4. Inputs provided in advance will be lost if not immediately used

```python
# This will NOT work:
await workflow.step({"future_node_id": "data"})  # Input for a node not yet halted
# ... later when the node halts ...
await workflow.step()  # The input is already gone!
```

## Example of an Agent Requiring Feedback

```python
class ContentReviewNode(Node):
    def prepare(self, shared, request_input):
        return {
            "content": shared.get("draft_content", ""),
            "request_input": request_input,
            "llm_client": shared.get("llm_client")
        }
    
    async def execute(self, prepared_data):
        request_input = prepared_data["request_input"]
        content = prepared_data["content"]
        llm_client = prepared_data["llm_client"]
        
        # First, get LLM suggestions
        prompt = f"Suggest improvements for this content:\n\n{content}"
        llm_response = await llm_client.generate(prompt)
        
        # Show suggestions to human for approval
        user_decision = await request_input(
            prompt="The AI suggests these improvements. Accept?",
            options=["Accept All", "Accept Some", "Reject All"],
            input_type="select",
            request_id="improvement_decision"
        )
        
        if user_decision == "Accept Some":
            # Request specific edits from human
            specific_edits = await request_input(
                prompt="Which specific changes would you like to make?",
                request_id="specific_edits"
            )
            
            # Second LLM call with human guidance
            refined_prompt = f"Revise this content:\n\n{content}\n\nWith these specific changes: {specific_edits}"
            final_content = await llm_client.generate(refined_prompt)
        elif user_decision == "Accept All":
            final_content = llm_response
        else:
            final_content = content
            
        return {"original": content, "final": final_content}
    
    def cleanup(self, shared, prepared_data, execution_result):
        shared["reviewed_content"] = execution_result["final"]
```
