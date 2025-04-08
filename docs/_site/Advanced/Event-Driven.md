
```markdown
# Making Your Workflow Event-Driven

## Overview

Sometimes you want your workflows to kick into action when something happens in the outside world. Maybe an order comes in, a temperature sensor hits a threshold, or your cat posts a new Instagram photo. Here's how to make your workflows respond to events, not just commands.

## Creating an Event Dispatcher

First, let's build a robust event dispatcher that can trigger workflows when events occur and persist trigger configurations:

```python
# event_dispatcher.py
import asyncio
import json
import os
from datetime import datetime
from typing import Dict, List, Any, Optional
from grapheteria import WorkflowEngine

class EventDispatcher:
    """Manages event subscriptions and dispatches events to workflows."""
    
    def __init__(self, storage_path="events"):
        self.storage_path = storage_path
        self.subscriptions = {}  # event_type -> list of workflow IDs
        self.active_workflows = {}  # (workflow_id, run_id) -> WorkflowEngine
        
        # Create storage directory if it doesn't exist
        os.makedirs(storage_path, exist_ok=True)
        
        # Load existing subscriptions
        self.load_triggers()
    
    def subscribe(self, event_type: str, workflow_id: str, config: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Subscribe a workflow to an event type with optional configuration."""
        if event_type not in self.subscriptions:
            self.subscriptions[event_type] = []
            
        # Create subscription record
        subscription = {
            "workflow_id": workflow_id,
            "config": config or {},
            "created_at": datetime.now().isoformat()
        }
        
        self.subscriptions[event_type].append(subscription)
        
        # Persist to storage
        self.save_triggers()
        
        return subscription
        
    def unsubscribe(self, event_type: str, workflow_id: str) -> bool:
        """Unsubscribe a workflow from an event type."""
        if event_type not in self.subscriptions:
            return False
            
        original_length = len(self.subscriptions[event_type])
        self.subscriptions[event_type] = [
            sub for sub in self.subscriptions[event_type] 
            if sub["workflow_id"] != workflow_id
        ]
        
        # If the list is empty, remove the event type
        if not self.subscriptions[event_type]:
            del self.subscriptions[event_type]
            
        # Persist changes
        self.save_triggers()
        
        # Return true if something was removed
        return len(self.subscriptions.get(event_type, [])) < original_length
    
    def get_subscriptions(self, event_type: str = None) -> Dict[str, List[Dict[str, Any]]]:
        """Get all subscriptions or subscriptions for a specific event type."""
        if event_type:
            return {event_type: self.subscriptions.get(event_type, [])}
        return self.subscriptions
    
    def save_triggers(self) -> None:
        """Save trigger configurations to filesystem."""
        triggers_file = os.path.join(self.storage_path, "triggers.json")
        
        # Use atomic write operation
        temp_file = f"{triggers_file}.tmp"
        with open(temp_file, 'w') as f:
            json.dump(self.subscriptions, f, indent=2)
        
        # Atomic rename
        os.rename(temp_file, triggers_file)
        
    def load_triggers(self) -> None:
        """Load trigger configurations from filesystem."""
        triggers_file = os.path.join(self.storage_path, "triggers.json")
        
        if os.path.exists(triggers_file):
            try:
                with open(triggers_file, 'r') as f:
                    self.subscriptions = json.load(f)
            except json.JSONDecodeError:
                # Handle corrupted file
                self.subscriptions = {}
        else:
            self.subscriptions = {}
    
    async def dispatch(self, event_type: str, payload: Any = None) -> List[Dict[str, Any]]:
        """Dispatch an event to all subscribed workflows."""
        results = []
        
        if event_type not in self.subscriptions:
            return results
            
        for subscription in self.subscriptions[event_type]:
            workflow_id = subscription["workflow_id"]
            config = subscription["config"]
            
            # Create workflow instance
            workflow = WorkflowEngine(workflow_id=workflow_id)
            run_id = workflow.run_id
            
            # Store in active workflows
            self.active_workflows[(workflow_id, run_id)] = workflow
            
            # Add event data to shared state
            workflow.execution_state.shared.update({
                "event_type": event_type,
                "event_payload": payload,
                "event_config": config,
                "event_time": datetime.now().isoformat()
            })
            
            # Run the workflow
            continuing, tracking_data = await workflow.run()
            
            results.append({
                "workflow_id": workflow_id,
                "run_id": run_id,
                "status": workflow.execution_state.workflow_status.name
            })
            
        return results
```

## Adding Event Routes to FastAPI

Now, let's extend your FastAPI application to handle event subscriptions and triggers:

```python
# routes.py
from fastapi import APIRouter, HTTPException, Body
from typing import Dict, Any, Optional
from pydantic import BaseModel
from event_dispatcher import EventDispatcher

router = APIRouter()
event_dispatcher = EventDispatcher()

# Event subscription model
class EventSubscription(BaseModel):
    workflow_id: str
    config: Optional[Dict[str, Any]] = None

@router.post("/events/subscribe/{event_type}")
async def subscribe_to_event(event_type: str, subscription: EventSubscription):
    """Subscribe a workflow to an event type."""
    result = event_dispatcher.subscribe(
        event_type, 
        subscription.workflow_id, 
        subscription.config
    )
    return {
        "message": f"Workflow {subscription.workflow_id} subscribed to event {event_type}",
        "subscription": result
    }

@router.delete("/events/unsubscribe/{event_type}")
async def unsubscribe_from_event(event_type: str, workflow_id: str):
    """Unsubscribe a workflow from an event type."""
    success = event_dispatcher.unsubscribe(event_type, workflow_id)
    if not success:
        raise HTTPException(status_code=404, detail=f"No subscription found for event {event_type} and workflow {workflow_id}")
    return {
        "message": f"Workflow {workflow_id} unsubscribed from event {event_type}"
    }

@router.get("/events")
async def list_events():
    """List all event subscriptions."""
    return event_dispatcher.get_subscriptions()

@router.get("/events/{event_type}")
async def get_event_subscriptions(event_type: str):
    """Get subscriptions for a specific event type."""
    subscriptions = event_dispatcher.get_subscriptions(event_type)
    if not subscriptions.get(event_type):
        raise HTTPException(status_code=404, detail=f"No subscriptions found for event {event_type}")
    return subscriptions

@router.post("/events/trigger/{event_type}")
async def trigger_event(event_type: str, payload: Optional[Dict[str, Any]] = Body(None)):
    """Trigger an event, executing all subscribed workflows."""
    results = await event_dispatcher.dispatch(event_type, payload)
    return {
        "message": f"Event {event_type} triggered",
        "workflows_executed": len(results),
        "results": results
    }
```

## Creating Webhook Triggers with Verification

For secure communication with external systems, let's add webhook support with signature verification:

```python
# webhook_routes.py
from fastapi import APIRouter, HTTPException, Request, Header, Depends
import json
import hmac
import hashlib
import os
from event_dispatcher import EventDispatcher

router = APIRouter()
event_dispatcher = EventDispatcher()

# Get webhook secret from environment (should be properly managed in production)
WEBHOOK_SECRET = os.environ.get("WEBHOOK_SECRET", "change-me-in-production")

async def verify_webhook_signature(
    request: Request, 
    x_signature: Optional[str] = Header(None, alias="X-Webhook-Signature")
):
    """Verify the webhook signature for authenticity."""
    if not x_signature:
        # You may want to make this mandatory in production
        return True
        
    # Get request body for signature validation
    body = await request.body()
    
    # Compute expected signature
    expected_signature = hmac.new(
        WEBHOOK_SECRET.encode(),
        body,
        hashlib.sha256
    ).hexdigest()
    
    # Verify using constant-time comparison
    if not hmac.compare_digest(expected_signature, x_signature):
        raise HTTPException(status_code=401, detail="Invalid webhook signature")
    
    return True

@router.post("/webhooks/{event_type}")
async def webhook_handler(
    event_type: str, 
    request: Request,
    verified: bool = Depends(verify_webhook_signature)
):
    """Handle webhook calls for specific event types with signature verification."""
    try:
        # Parse the payload
        body = await request.body()
        if not body:
            payload = {}
        else:
            try:
                payload = json.loads(body)
            except json.JSONDecodeError:
                payload = {"raw_body": body.decode("utf-8", errors="replace")}
        
        # Add headers and query params to payload
        payload["headers"] = dict(request.headers)
        payload["query_params"] = dict(request.query_params)
        
        # Dispatch the event
        results = await event_dispatcher.dispatch(event_type, payload)
        
        return {
            "status": "success",
            "event_type": event_type,
            "workflows_triggered": len(results)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Webhook processing failed: {str(e)}")
```

## Scheduled Events with Background Tasks

Want to trigger workflows on a schedule? Let's use FastAPI's background tasks:

```python
# scheduler.py
from fastapi import FastAPI, BackgroundTasks, HTTPException, Body
import asyncio
from datetime import datetime
from typing import Dict, Any, Optional
from event_dispatcher import EventDispatcher

app = FastAPI()
event_dispatcher = EventDispatcher()
scheduled_tasks = {}

async def run_scheduled_event(event_type, payload, interval_seconds):
    """Run an event on a schedule."""
    while True:
        try:
            await event_dispatcher.dispatch(event_type, payload)
            # Update payload with last_run timestamp
            if isinstance(payload, dict):
                payload["last_run"] = datetime.now().isoformat()
        except Exception as e:
            print(f"Error in scheduled event {event_type}: {str(e)}")
        
        await asyncio.sleep(interval_seconds)

@app.post("/schedule/{event_type}")
async def schedule_event(
    event_type: str,
    interval_seconds: int,
    background_tasks: BackgroundTasks,
    payload: Optional[Dict[str, Any]] = Body(None)
):
    """Schedule an event to run periodically."""
    if event_type in scheduled_tasks:
        return {"message": f"Event {event_type} already scheduled"}
    
    if interval_seconds < 5:  # Reasonable minimum in production
        raise HTTPException(status_code=400, detail="Interval must be at least 5 seconds")
    
    # Initialize payload if None
    actual_payload = payload or {}
    actual_payload["scheduled_at"] = datetime.now().isoformat()
    
    task = asyncio.create_task(run_scheduled_event(event_type, actual_payload, interval_seconds))
    scheduled_tasks[event_type] = {
        "task": task,
        "interval": interval_seconds,
        "payload": actual_payload,
        "started_at": datetime.now().isoformat()
    }
    
    return {
        "message": f"Event {event_type} scheduled to run every {interval_seconds} seconds",
        "event_type": event_type,
        "interval_seconds": interval_seconds
    }

@app.delete("/schedule/{event_type}")
async def cancel_scheduled_event(event_type: str):
    """Cancel a scheduled event."""
    if event_type not in scheduled_tasks:
        raise HTTPException(status_code=404, detail=f"No scheduled event found for {event_type}")
    
    task_info = scheduled_tasks[event_type]
    task_info["task"].cancel()
    del scheduled_tasks[event_type]
    
    return {
        "message": f"Scheduled event {event_type} cancelled",
        "event_type": event_type
    }

@app.get("/schedule")
async def list_scheduled_events():
    """List all scheduled events."""
    result = {}
    for event_type, task_info in scheduled_tasks.items():
        result[event_type] = {
            "interval_seconds": task_info["interval"],
            "started_at": task_info["started_at"],
            "payload": task_info["payload"]
        }
    return result
```

## Using the Event System

Here's how to put all this together:

```python
# main.py
from fastapi import FastAPI
from routes import router as api_router
from webhook_routes import router as webhook_router
from scheduler import app as scheduler_app

app = FastAPI()

# Regular API routes
app.include_router(api_router, prefix="/api")

# Webhook routes - no prefix for easier external access
app.include_router(webhook_router)

# Include scheduler routes
app.include_router(scheduler_app, prefix="/api")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
```

## Practical Examples

### Example 1: Responding to a Payment Event

Subscribe to payment events:
```python
import requests

# Register a workflow to process orders when payment is received
response = requests.post(
    "https://your-api.com/api/events/subscribe/payment_received",
    json={
        "workflow_id": "order_processing",
        "config": {
            "priority": "high",
            "notify_on_completion": True
        }
    }
)
```

Trigger a payment event:
```python
import requests

# Trigger the event when payment is confirmed
response = requests.post(
    "https://your-api.com/api/events/trigger/payment_received",
    json={
        "order_id": "12345",
        "amount": 99.99,
        "currency": "USD",
        "payment_method": "credit_card"
    }
)
```

### Example 2: Setting Up a GitHub Webhook with Signature Verification

1. Generate a secure webhook secret and configure it in your environment:
   ```
   export WEBHOOK_SECRET=your-secure-secret-key
   ```

2. Configure your GitHub repository webhook settings:
   - URL: `https://your-api.com/webhooks/github_push`
   - Content type: `application/json`
   - Secret: Same as your `WEBHOOK_SECRET`
   - Events: Select "Push" events

3. Subscribe your workflow:
   ```python
   import requests
   
   response = requests.post(
       "https://your-api.com/api/events/subscribe/github_push",
       json={
           "workflow_id": "auto_deploy",
           "config": {
               "branches": ["main", "production"],
               "deploy_target": "production"
           }
       }
   )
   ```

4. Verify your webhook is working:
   ```python
   import requests
   
   response = requests.get(
       "https://your-api.com/webhooks/github_push/test"
   )
   ```

### Example 3: Scheduling a Daily Report

```python
import requests

# Schedule a report generation event to run daily
response = requests.post(
    "https://your-api.com/api/schedule/generate_daily_report",
    json={
        "interval_seconds": 86400,  # 24 hours
        "payload": {
            "report_type": "sales_summary",
            "recipients": ["team@company.com"]
        }
    }
)
```

## Wrapping Up

With this event system, your workflows can spring to life at just the right moment. The persistent storage ensures your event subscriptions survive system restarts, while signature verification keeps your webhooks secure. Whether it's responding to API calls, webhooks from external services, or running on a schedule, you've got the tools to make your state machine truly event-driven.

Remember, the best automation is the kind you don't have to think about - it just happens when it should!
```
