---
layout: default
title: "State Machines"
parent: "Concepts"
nav_order: 1
---
# The Magic of State Machines: Building Intelligent Workflows

## Overview

Grapheteria uses something called "finite state machines" to create workflows that can act on their own (that's what "agentic" means). Think of it as building a flow chart where each step (node) connects to other steps through paths (edges), creating a system that can make decisions and do tasks automatically.

## What's a State Machine?

Imagine a traffic light. It can only be in one state at a time: red, yellow, or green. After a set time, it changes from one state to another in a specific order. That's a simple state machine!

Another example is your washing machine:
- It starts in the "off" state
- You put in clothes and press start → it moves to the "washing" state
- After washing, it automatically moves to the "rinsing" state
- Then it goes to the "spinning" state
- Finally, it returns to the "off" state

State machines are all around us - they're just systems that can be in exactly one state at any time, with clear rules about how they move between states.

## Grapheteria's Implementation

In Grapheteria, we build these state machines as workflows:

```python
# Create two simple steps (nodes)
check_weather = WeatherNode(id="check_weather")
decide_activity = DecisionNode(id="decide_activity")

# Connect them (the arrow means "go from this step to that step")
check_weather > decide_activity

# Or make the connection depend on certain conditions
check_weather - "shared['weather'] == 'sunny'" > go_to_beach
check_weather - "shared['weather'] == 'rainy'" > stay_indoors
```
> Don't worry if this syntax looks unfamiliar or if you're wondering what `shared` refers to. We'll cover all that later! This example shows how to create a conditional connection between nodes. The pattern follows: from_node - "condition" > to_node
{: .note}

### Nodes as States

A node is just a single step in your workflow. Each node has one job:
- Get the weather forecast
- Ask a human for input
- Decide what to do next
- Generate a response using AI

Think of each node like a station in an assembly line - it does its specific task, then passes things along to the next station.

### Edges as Transitions

Edges are the connections between nodes - they're like the conveyor belts in our assembly line example. What makes them special is they can have conditions:

```python
payment_check - "payment_successful" > send_confirmation
payment_check - "payment_failed" > retry_payment
```

This means your workflow can take different paths depending on what happens at each step - just like how you might take a different route home if there's traffic on your usual road.

## Why a State Machine?

Why do we build workflows this way? Because it makes complicated things simple:

1. **Easy to Understand**: You can draw your workflow on a piece of paper with boxes and arrows. Anyone can understand it without knowing code.

2. **Mirrors Real Life**: When you make breakfast, you're following a workflow: get eggs → crack eggs → cook eggs → serve eggs. Life is full of workflows!

3. **Reliable**: State machines always behave the same way given the same inputs, making them dependable.

4. **Can Pause and Resume**: Imagine if your GPS could pause during your road trip and continue exactly where you left off next week. Grapheteria workflows can do that:

```python
# Pick up a workflow where you left off
engine = WorkflowEngine(
    workflow_id="signup_process",
    run_id="20230615_103045"
)

# Continue running it
is_active, data = await engine.run()
```

State machines give you a simple way to build powerful systems that can handle complex tasks. They're like Lego blocks for creating processes that work exactly how you want them to.