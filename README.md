<div align="center">
  <img src="docs/assets/grapheteria.gif"/>
</div>

![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)
[![Docs](https://img.shields.io/badge/docs-latest-blue)](https://beubax.github.io/Grapheteria/)

## What is Grapheteria?

A structured agentic workflow framework bringing uniformity to agent orchestration:
- 🎨 Design complex agent topologies with standardized visual primitives
- 💻 Implement workflows with a consistent, inheritance-free API
- ⏰ Debug execution graphs with deterministic state tracking
- 🚀 Deploy scalable systems without abstraction overhead

"Oh no 😵‍💫, not ANOTHER workflow library! " - I hear you. But being fashionably late means we've learned from everyone else's mistakes and cherry-picked their best ideas, while adding our own secret sauce.

<div align="center">
  <img src="docs/assets/workflow-concept.png"/>
</div>

## How is it different?

While agent creation and tool-calling have standards, workflow creation is still a mess. Grapheteria fixes that with a clean framework that gives you what you need while letting you extend things however you want.

### Problems with Existing Tools

**Code-based workflow builders** make your brain hurt:
- "Wait, what does this wrapper do again?" 
- "How many layers of inheritance am I dealing with?"
- "I just want to see what's happening!"

**UI-only tools** hit walls quickly:
- Can't customize for complex scenarios
- Multi-agent setups? Forget about it
- You eventually crawl back to code anyway

## The Vision: Best of Both Worlds

Grapheteria blends code and UI seamlessly. Bounce between visual design and code customization without compromises. Get all the power of code with the clarity of visual debugging.

![Code-UI Sync](docs/assets/workflow.png)
<!-- An animated GIF showing changes in code immediately reflected in the UI and vice versa -->

## Standout Features

### Clean, Simple Code
Write workflows without a PhD in API-ology:

```python
start_node = InputNode(id="get_name")
process_node = ProcessNode(id="greet")
output_node = OutputNode(id="display")

start_node > process_node > output_node
```

### Powerful Agentic Patterns
Build sophisticated agent architectures with proven patterns:
- Chain-of-Thought: Break down complex reasoning into sequential steps
- Verification Loops: Self-check outputs with critic agents
- Parallel Processing: Distribute tasks across multiple specialized agents
- ReAct Framework: Integrate reasoning and action loops seamlessly
- Human-in-the-Loop: Add supervision exactly where needed

```mermaid
%%{init: {'theme': 'neutral' }}%%
graph TD
    %% Chain of Thought
    subgraph "Chain of Thought"
    A1[Task Input] --> B1[Reasoning Step 1]
    B1 --> C1[Reasoning Step 2]
    C1 --> D1[Reasoning Step 3]
    D1 --> E1[Final Output]
    end
    
    %% Verification Loop
    subgraph "Verification Loop"
    A2[Input] --> B2[Generator]
    B2 --> C2[Critic]
    C2 -->|Pass| D2[Output]
    C2 -->|Fail| B2
    end
    
    %% Parallel Processing
    subgraph "Parallel Processing"
    A3[Task] --> B3[Splitter]
    B3 --> C3[Agent 1]
    B3 --> D3[Agent 2]
    B3 --> E3[Agent 3]
    C3 & D3 & E3 --> F3[Aggregator]
    F3 --> G3[Result]
    end
    
    %% ReAct Framework
    subgraph "ReAct Framework"
    A4[Problem] --> B4[Reason]
    B4 --> C4[Act]
    C4 --> D4[Observe]
    D4 -->|Repeat| B4
    D4 -->|Complete| E4[Solution]
    end
    
    %% Human-in-the-Loop
    subgraph "Human-in-the-Loop"
    A5[Input] --> B5[Agent Process]
    B5 -->|Uncertain| C5[Human Review]
    C5 --> D5[Incorporate Feedback]
    D5 --> B5
    B5 -->|Confident| E5[Output]
    end
```

### Visual Workflow Design
Edit visually or with code - they stay perfectly in sync!
- Drop nodes right in the UI
- Reroute your flow with a few clicks
- Debug in real-time while tweaking code
- Switch between code and UI whenever you want

![Workflow Editor](docs/assets/code_sync.gif)
<!-- A screenshot of the Grapheteria workflow editor with nodes, edges, and a properties panel -->

### Time-Travel Debugging
Made a mistake? No sweat:
- Step backward in time
- Fix the bug
- Step forward
- Keep going from exactly where you left off

![Time Travel Debug](docs/assets/debug.gif)
<!-- An animated GIF showing someone debugging, going back in time, fixing a node, and continuing -->

### Built-in Essentials
- Super detailed logging
- Auto-saves your state
- Easy resume after stopping

![Logging Demo](docs/assets/tracking.png)
<!-- A screenshot showing logs and state persistence in action -->

### Production-Ready Path
From your laptop to the cloud with minimal changes:
- Scale to distributed execution
- Track everything automatically
- Handle errors like a pro

![Scaling Diagram](docs/assets/scaling.png)
<!-- An illustration showing workflow scaling from local to distributed environments -->

### Vibe-Coding Compatible
Describe what you want, then fine-tune:
- Generate workflows with AI
- Tweak instead of starting from scratch
- Build complex flows in minutes, not hours

![LLM Generation](docs/assets/llm_generate.gif)
<!-- An animated GIF showing a text prompt being turned into a workflow -->

## Ready to Try It?

### Installation

```bash
# Create a virtual environment (recommended)
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install Grapheteria
pip install grapheteria
```

> **Note:** Grapheteria requires Python 3.6 or higher.

### Launch the UI

Once installed, fire up the UI with:

```bash
grapheteria
```
This starts the Grapheteria interface and automatically syncs with your code.

<div class="d-flex justify-content-center mt-4">
  <a href="Core" class="btn btn-primary btn-sm px-2 py-2 mb-4">Learn Core Concepts →</a>
</div>
