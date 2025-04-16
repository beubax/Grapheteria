---
layout: default
title: "Troubleshooting"
parent: "UI"
nav_order: 4
---

# Troubleshooting Grapheteria

## Overview

Welcome to the troubleshooting section! As more people try Grapheteria, we'll keep adding commonly faced issues (and keep trying to fix them, of course!). The golden rule of bug fixing: when things go from bad to worse, a good old server restart fixes most issues. A restart triggers a fresh scan of all workflows and nodes in your directory, ensuring you're working with the latest data. Not ideal, but effective!

## Module Loading Errors

If your Python module containing node definitions has errors, it won't load properly:

```python
# This broken code will prevent nodes from being registered
class MyBrokenNode(Node):
    def execute(self, prepared_result)  # Missing colon here!
        return "This won't work"
```

**Symptoms:**
- Nodes don't appear in the UI
- Old versions of nodes show up instead of your updates
- Deleted nodes stubbornly remain in the UI

**Solution:** Check for syntax errors in your Python files. The compiler's red squiggles are your friends here! Fix any syntax issues and re-save the file.

## Deleted Node Classes

When you delete a node class from your Python code, it may haunt your UI:

```python
# If you delete this from your code...
class DataProcessorNode(Node):
    async def execute(self, prepared_result):
        return process_data(prepared_result)
```

The node will continue to appear in your workflow until you explicitly remove it from the UI or the JSON file.

**Why?** This preserves your workflow structure in case you accidentally delete code. Automatic removal would cascade to connected edges and potentially break your workflow.

**Solution:** Manually delete unwanted nodes from the UI canvas or edit your workflow JSON file.

## File Renaming Adventures

Renaming files can lead to unexpected behavior:

**What happens:** The server tracks each file and its nodes in a dictionary structure. When you rename a file:
1. The old filename entry remains in the server's memory
2. A new entry is created for the new filename 
3. This causes node duplication in the tracking system

This duplication can lead to unexpected behavior, like nodes appearing twice or importing failures.

**Solution:** After renaming files, restart the server to clear its internal file registry and rebuild it from scratch.

## Duplicate Node Names

Having multiple node classes with the same name across different files creates confusion:

```python
# In file1.py
class ProcessorNode(Node):
    # Does one thing

# In file2.py
class ProcessorNode(Node):  # Same name!
    # Does something entirely different
```

**What happens:** Only one version will appear in the UI - typically the last one scanned. This behavior isn't deterministic and can lead to unexpected workflow behavior.

**Solution:** Use unique, descriptive names for your node classes:

```python
# Better naming
class TextProcessorNode(Node): ...
class ImageProcessorNode(Node): ...
```

## The Universal Fix: Server Restart

When all else fails, restart your server:

```bash
# Stop current server (Ctrl+C)
grapheteria
```

This ensures all your code is freshly scanned and registered properly.

## Getting Help

Encountered an issue not covered here? Please report it on our [GitHub Issues page](https://github.com/beubax/grapheteria/issues). Your feedback helps make Grapheteria better for everyone!

Happy graph-building! 🚀
