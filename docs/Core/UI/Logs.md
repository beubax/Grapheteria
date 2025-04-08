# Logs

## Overview

The logs tab is your time machine for workflows. It lets you peek into the past, present, and alternate timelines of every workflow you've created. Here you can track every step, decision, and path your workflows have taken throughout their journey.

![Overview of the Logs tab interface](placeholder-logs-overview.png)

Currently, logs are stored on your local filesystem (we're working on fancy database options soon, we promise!).

## Selecting Workflows

Finding the workflow you're looking for is a breeze. Simply:

1. Navigate to the logs tab
2. Browse the list of available workflows
3. Click on any workflow that catches your eye

Each workflow displays its run history - a collection of timestamps that serve as both run IDs and breadcrumbs showing when each execution occurred.

![Workflow selection interface](placeholder-workflow-selection.png)

## Exploring Run Details

Clicked on a run and ready to dive deeper? Each run reveals its secrets:

- Workflow ID
- Run ID
- Detailed execution steps
- Previous node ID
- Next node ID
- Awaiting nodes
- ...and much more fascinating data!

Think of it as a workflow's diary - recording every thought, action, and decision it made during its execution.

![Run details view](placeholder-run-details.png)

## Tracking Workflow Evolution

Sometimes workflows branch into new variations - like alternate timelines in a sci-fi movie. When a workflow was forked from a previous run, you'll see:

- A clickable link to the parent run at the top
- Detailed metadata showing exactly where and how the fork happened

This feature is particularly handy when you're experimenting with different workflow paths or debugging complex processes.

![Workflow fork tracking](placeholder-workflow-fork.png)

Ready to become a workflow time traveler? The logs tab awaits your exploration!

<img src="bruh.png" width="450" height="800" />
