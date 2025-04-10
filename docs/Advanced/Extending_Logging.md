---
layout: default
title: "Extending Logging System"
parent: "Advanced"
nav_order: 2
---

# Extending the Logging System

## Where Do Your Workflows Go When They Sleep?

By default, Grapheteria stores all your workflow logs in the local filesystem. This works great for development, but when you're ready for the big leagues (aka production), you might want something more robust. Maybe you need centralized storage, better querying capabilities, or just don't trust those pesky local files (we've all accidentally `rm -rf`'d something important, right?).

## Tracking Data: The Memory of Your Workflows

Every workflow maintains a `tracking_data` structure that contains:

```python
{
    "workflow_id": "your.awesome.workflow",
    "run_id": "20230415_120523_123",
    "steps": [
        # State snapshot after each step execution
        # Each containing everything needed to resume execution
    ]
}
```

The `steps` list is particularly magical - it captures the complete execution state after each node runs. This is what enables our workflow to pick up exactly where it left off, even if your server decided to take an unplanned vacation.

> At the end of every step, the workflow engine calls `self.storage.save_state()` with the storage object being whatever custom backend you decide to provide (defaults to local file system)
{: .important}

## Creating Your Own Storage Backend

The `StorageBackend` abstract class defines the interface any storage implementation must follow:

```python
class StorageBackend(ABC):
    @abstractmethod
    def save_state(self, workflow_id: str, run_id: str, tracking_data: dict) -> None:
        """Save the workflow execution state."""
        pass
    
    @abstractmethod
    def load_state(self, workflow_id: str, run_id: str) -> Optional[Dict]:
        """Load a workflow execution state."""
        pass

    @abstractmethod
    def list_runs(self, workflow_id: str) -> List[str]:
        """List all runs for a given workflow."""
        pass

    @abstractmethod
    def list_workflows(self) -> List[str]:
        """List all workflows."""
        pass
```

Let's break down these methods:

- `save_state`: Stores the workflow state with its unique identifiers
- `load_state`: Retrieves the state of a specific workflow run
- `list_runs`: Gets all runs for a specific workflow (useful for history/debugging)
- `list_workflows`: Lists all available workflows in the storage

## Example: SQLite Storage Implementation

Here's an example of implementing SQLite storage - observe how it satisfies the same interface:

```python
from grapheteria.utils import StorageBackend

class SQLiteStorage(StorageBackend):
    def __init__(self, db_path: str = "workflows.db"):
        self.db_path = db_path
        self._init_db()
        
    def _init_db(self):
        # Creates the database table if it doesn't exist
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS workflow_states (
                workflow_id TEXT,
                run_id TEXT,
                state_json TEXT,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY (workflow_id, run_id)
            )
            ''')
            conn.commit()
    
    @contextmanager
    def _get_connection(self):
        conn = sqlite3.connect(self.db_path)
        try:
            yield conn
        finally:
            conn.close()
    
    def save_state(self, workflow_id: str, run_id: str, source_data: dict) -> None:
        # Saves workflow state as JSON in the database
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                '''
                INSERT OR REPLACE INTO workflow_states (workflow_id, run_id, state_json, updated_at)
                VALUES (?, ?, ?, CURRENT_TIMESTAMP)
                ''',
                (workflow_id, run_id, json.dumps(source_data))
            )
            conn.commit()
            
    def load_state(self, workflow_id: str, run_id: str) -> Optional[Dict]:
        # Retrieves workflow state from the database
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT state_json FROM workflow_states WHERE workflow_id = ? AND run_id = ?",
                (workflow_id, run_id)
            )
            row = cursor.fetchone()
            
        if not row:
            return None
            
        return json.loads(row[0])
```

Using the SQLite backend is as simple as:

```python
# Initialize the workflow engine with SQLite storage
storage = SQLiteStorage("production.db")
engine = WorkflowEngine(
    workflow_id="my.workflow",
    storage_backend=storage
)

# Now all state is stored in SQLite!
```

## Creating Your Own Storage

Want to store workflows in Redis, MongoDB, or your secret underground bunker's mainframe? Just implement those four methods and you're good to go!

Here's a stub for your next storage adventure:

```python
class MyAwesomeStorage(StorageBackend):
    def __init__(self, connection_string):
        # Connect to your storage service
        self.client = AwesomeStorageClient(connection_string)
    
    def save_state(self, workflow_id, run_id, source_data):
        # Your code to save state
        self.client.upsert_document(
            collection="workflows",
            key=f"{workflow_id}:{run_id}",
            data=source_data
        )
    
    # Implement the other required methods...
```

Now your workflows can live wherever they want - give them the freedom they deserve!