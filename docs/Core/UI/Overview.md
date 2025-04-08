# The UI: Visual Workflow Management

## Overview: Meet the UI

Welcome to the visual side of Grapheteria! The UI connects to your codebase through websockets, making your workflow design interactive and intuitive.

To get started, run this command in your terminal:

'''
grapheteria
'''

This simple command launches both the server and UI. Now you can visually manage all your nodes, create connections, configure them, and debug your workflows with ease.

![Screenshot of Grapheteria UI homepage](placeholder-for-ui-homepage.png)

## Discovering Your Components

When launched, the server automatically scans your working directory for:
- Any nodes you've created (classes extending the Node class)
- Existing workflows (stored as JSON files)

Everything is instantly available in your browser - no manual importing needed!

![Workflow selection screen](placeholder-for-workflow-selection.png)

## Canvas: Your Workflow Playground

After selecting or creating a workflow, you'll see your canvas - the blank slate for your state machine.

Need to add nodes? Just right-click anywhere on the canvas to see all available nodes. Each node you add automatically updates your workflow's JSON schema.

![Canvas with right-click menu showing available nodes](placeholder-for-canvas-rightclick.png)

## Building Your State Machine

### Adding and Configuring Nodes
Add as many nodes as your workflow needs. Right-click on any node to:
- Set it as the start node
- Modify its configuration
- View its source code
- And more!

### Creating Connections
Connect your nodes by dragging from the center of one node to another. An edge appears, linking them together - and yes, your JSON file updates in real-time!

![Connecting nodes with edges](placeholder-for-edge-creation.png)

### Removing Components
To delete a node or edge:
- Double-click on a node's handle (the same handle lets you drag nodes around)
- Double-click anywhere on an edge to remove it

### Edge Configuration
Edges aren't just connections - click the button on any edge to add transition conditions.

![Edge with condition button highlighted](placeholder-for-edge-condition.png)

## Setting Initial State

Look for the button at the bottom of your canvas to set your workflow's initial state - crucial for proper execution!

![Initial state configuration](placeholder-for-initial-state.png)

## Real-Time Synchronization

Keep an eye on the connection icon in the top left. Green means you're connected and changes are syncing to your JSON file.

The UI only shows what's actually in your schema. If something doesn't appear as expected, check the connection status - your progress is always safe.

![Connection status indicator](placeholder-for-connection-status.png)

## Ready to Run

Once your workflow looks good, head to the debug/run tab on the middle right of the screen. There you can test your state machine and see it in action!

[Learn more about debugging and running workflows](placeholder-link-to-debug-doc)

![Debug tab location](placeholder-for-debug-tab.png)

## Troubleshooting

Having issues? Check out our troubleshooting guide for common problems and solutions.

[Troubleshooting Guide](placeholder-link-to-troubleshoot-doc)