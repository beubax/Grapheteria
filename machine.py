from dataclasses import dataclass, field
from typing import Callable, Dict, Any, Optional, List, Type, ClassVar, Set
from enum import Enum, auto
from datetime import datetime
import time
import copy
import json
import asyncio
from abc import ABC, abstractmethod
import inspect
import os
from uuid import uuid4
import glob
import logging
# At the top of machine.py, before the class definitions
_NODE_REGISTRY: Dict[str, Type['Node']] = {}

class WorkflowStatus(Enum):
    """Represents the overall status of a workflow."""
    NOT_STARTED = auto()
    RUNNING = auto()
    COMPLETED = auto()
    FAILED = auto()

class NodeStatus(str, Enum):
    """Represents the current status of a node during execution."""
    PENDING = "pending"
    ACTIVE = "active"
    WAITING_FOR_INPUT = "waiting_for_input"
    COMPLETED = "completed"
    FAILED = "failed"

@dataclass
class ExecutionState:
    """Represents the complete state of a workflow execution."""
    shared: Dict[str, Any]
    current_node_ids: Set[str]
    node_statuses: Dict[str, NodeStatus]
    history: List[Dict[str, Any]]
    workflow_status: WorkflowStatus
    awaiting_inputs: Optional[Dict[str, Dict[str, Any]]] = None
    input_data: Optional[Dict[str, Any]] = None
    previous_node_ids: Set[str] = field(default_factory=set)  # Track nodes from previous step

    def to_dict(self) -> dict:
        return {
            'shared': self.shared,
            'current_node_ids': list(self.current_node_ids),
            'node_statuses': {k: v.value for k, v in self.node_statuses.items()},
            'history': self.history,
            'workflow_status': self.workflow_status.name,
            'input_data': self.input_data,
            'awaiting_inputs': {k: v for k, v in self.awaiting_inputs.items()} if self.awaiting_inputs else None,
            'previous_node_ids': list(self.previous_node_ids)
        }

    @classmethod
    def from_dict(cls, data: dict) -> 'ExecutionState':
        return cls(
            shared=data['shared'],
            current_node_ids=set(data['current_node_ids']),
            node_statuses={k: NodeStatus(v) for k, v in data['node_statuses'].items()},
            history=data['history'],
            workflow_status=WorkflowStatus[data['workflow_status']],
            input_data=data.get('input_data'),
            awaiting_inputs={k: v for k, v in data.get('awaiting_inputs', {})} if data.get('awaiting_inputs') else None,
            previous_node_ids=set(data.get('previous_node_ids', []))
        )

class InputRequest:
    """Represents a request for human input"""
    def __init__(self, node_id, request_type, prompt=None, options=None):
        self.node_id = node_id
        self.request_type = request_type
        self.prompt = prompt
        self.options = options

class Node(ABC):
    """Unified base class for all nodes"""
    def __init__(self, id: Optional[str] = None, config: Optional[Dict[str, Any]] = None, 
                 max_retries: int = 1, wait: float = 0):
        self.id = id or f"{self.__class__.__name__}_{id(self)}"
        self.type = self.__class__.__name__
        self.config = config or {}
        self.transitions: Dict[str, 'Transition'] = {}
        self.max_retries = max_retries
        self.wait = wait
        self.cur_retry = 0

    def __init_subclass__(cls, **kwargs):
        """Auto-register nodes"""
        super().__init_subclass__(**kwargs)
        if not inspect.isabstract(cls):
            _NODE_REGISTRY[cls.__name__] = cls

    @classmethod
    def get_registry(cls) -> Dict[str, Type['Node']]:
        return _NODE_REGISTRY

    @classmethod
    def clear_registry(cls) -> None:
        _NODE_REGISTRY.clear()

    def get_next_node_ids(self, state: ExecutionState) -> Set[str]:
        return {
            transition.to_id 
            for transition in self.transitions.values() 
            if transition.should_transition(state)
        }

    def add_transition(self, transition: 'Transition') -> None:
        self.transitions[transition.to_id] = transition
        
    @classmethod
    def from_dict(cls, data: dict) -> 'Node':
        """Factory method to create appropriate node type"""
        node_type = cls.get_registry().get(data['class'])
        if not node_type:
            raise ValueError(
                f"Unknown node type: {data['class']}. "
                f"Available types: {', '.join(sorted(cls.get_registry().keys()))}"
            )
        return node_type(id=data['id'], config=data.get('config', {}))

    async def run(self, state: ExecutionState, request_input: Callable[[str, str, str, str], Any]) -> Any:
        
        state.node_statuses[self.id] = NodeStatus.ACTIVE
        
        # Pass the request_input function to prepare instead of the queue
        prep_result = self.prepare(state.shared, request_input)
        prepared_result = await prep_result if inspect.isawaitable(prep_result) else prep_result
        
        for self.cur_retry in range(self.max_retries):
            try:
                # Handle both sync and async execution automatically
                result = self.execute(prepared_result)
                execution_result = await result if inspect.isawaitable(result) else result
                
                state.node_statuses[self.id] = NodeStatus.COMPLETED
                cleanup_result = self.cleanup(state.shared, prepared_result, execution_result)
                return await cleanup_result if inspect.isawaitable(cleanup_result) else cleanup_result
                
            except Exception as e:
                if self.cur_retry == self.max_retries - 1:
                    state.node_statuses[self.id] = NodeStatus.FAILED
                    fallback_result = self.exec_fallback(prepared_result, e)
                    return await fallback_result if inspect.isawaitable(fallback_result) else fallback_result
                if self.wait > 0:
                    await asyncio.sleep(self.wait)
        return None

    def prepare(self, shared: Dict[str, Any], request_input: Any) -> Any:
        return None

    @abstractmethod
    def execute(self, prepared_result: Any) -> Any:
        pass

    def cleanup(self, shared: Dict[str, Any], prepared_result: Any, execution_result: Any) -> Any:
        return execution_result

    def exec_fallback(self, prepared_result: Any, e: Exception) -> Any:
        raise e

class Transition:
    def __init__(self, from_id: str, to_id: str, condition: str = "True"):
        self.from_id = from_id
        self.to_id = to_id
        self.condition = condition

    def should_transition(self, state: ExecutionState) -> bool:
        try:
            return eval(
                self.condition,
                {"__builtins__": {}},
                {"shared": state.shared, "True": True, "False": False, "None": None}
            )
        except Exception as e:
            print(f"Error evaluating condition '{self.condition}': {str(e)}")
            return False

    @classmethod
    def from_dict(cls, data: dict) -> 'Transition':
        return cls(
            from_id=data['from'],
            to_id=data['to'],
            condition=data.get('condition', 'True')
        )

class WorkflowEngine:
    def __init__(self, 
                 json_path: Optional[str] = None,
                 nodes_dict: Optional[Dict[str, Node]] = None, 
                 start_node_id: Optional[str] = None,
                 workflow_id: Optional[str] = None, 
                 workflow_name: Optional[str] = None,
                 initial_shared_state: Optional[Dict[str, Any]] = None,
                 max_parallel_nodes: int = 10,
                 run_id: Optional[str] = None,
                 auto_resume: bool = False,
                 resume_timestamp: Optional[str] = None):
        # Load from JSON if path provided
        if json_path:
            with open(json_path, "r") as f:
                data = json.load(f)
                
            # Extract workflow definition
            nodes_dict = {
                node_data['id']: Node.from_dict(node_data) 
                for node_data in data['nodes']
            }
            
            # Add transitions
            for edge_data in data['edges']:
                transition = Transition.from_dict(edge_data)
                source_node = nodes_dict[transition.from_id]
                source_node.add_transition(transition)
                
            # Set other parameters from JSON
            start_node_id = data['start']
            workflow_id = data['workflow_id']
            workflow_name = data.get('workflow_name')
            initial_shared_state = data.get('initial_state', {})
            max_parallel_nodes = data.get('max_parallel_nodes', max_parallel_nodes)
        
        # Validate required parameters
        if not nodes_dict or not start_node_id or not workflow_id:
            raise ValueError("Must provide json_path and (nodes_dict, start_node_id, and workflow_id)")
            
        # Initialize workflow properties
        self.nodes = nodes_dict
        self.start_node_id = start_node_id
        self.workflow_id = workflow_id
        self.workflow_name = workflow_name or workflow_id
        self.max_parallel_nodes = max_parallel_nodes
        self.run_id = run_id or f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_{uuid4().hex[:8]}"
        self.communication_queues = {}
        
        # Set up logging directory
        self.log_dir = f"logs/{self.workflow_id}/{self.run_id}"
        os.makedirs(self.log_dir, exist_ok=True)
        
        # Handle state initialization/resumption
        if resume_timestamp:
            self._resume_from_timestamp(resume_timestamp)
        elif auto_resume:
            self._resume_latest()
        else:
            self.execution_state = ExecutionState(
                shared=initial_shared_state or {},
                current_node_ids={start_node_id},
                node_statuses={},
                history=[],
                workflow_status=WorkflowStatus.NOT_STARTED
            )

        # Keep futures separate from serializable state
        self._input_futures = {}

    def _resume_latest(self):
        """Resume from the most recent state in the run directory"""
        state_files = sorted(
            [f for f in os.listdir(self.log_dir) if f.startswith("state_")],
            key=lambda x: os.path.getmtime(os.path.join(self.log_dir, x)),
            reverse=True
        )
        if not state_files:
            raise FileNotFoundError(f"No state files found in {self.log_dir}")
        self.load_state(os.path.join(self.log_dir, state_files[0]))

    def _resume_from_timestamp(self, timestamp: str):
        """Optimized timestamp resumption with direct string comparison"""
        # Fast path for exact match
        exact_path = os.path.join(self.log_dir, f"state_{timestamp}.json")
        if os.path.exists(exact_path):
            self.load_state(exact_path)
            self._purge_newer_states(timestamp)
            return
            
        # Efficient partial match without glob
        try:
            state_files = sorted([
                f for f in os.listdir(self.log_dir) 
                if f.startswith(f"state_{timestamp}") and f.endswith(".json")
            ], reverse=True)
            
            if not state_files:
                raise FileNotFoundError()
                
            self.load_state(os.path.join(self.log_dir, state_files[0]))
            loaded_timestamp = state_files[0].split("_")[1].split(".")[0]
            self._purge_newer_states(loaded_timestamp)
            
        except (FileNotFoundError, IndexError):
            # Optimized available timestamps listing
            available = sorted([
                f.split("_")[1].split(".")[0] 
                for f in os.listdir(self.log_dir) 
                if f.startswith("state_") and f.endswith(".json")
            ])[:10]  # Limit to 10 for display
            
            raise FileNotFoundError(
                f"No state file matching '{timestamp}'. "
                f"Available timestamps: {', '.join(available)}"
                f"{' and more...' if len(available) == 10 else ''}"
            )

    def _purge_newer_states(self, loaded_timestamp: str):
        """Optimized purging using direct string comparison"""
        # Direct string comparison is faster than datetime parsing
        # Our timestamp format (YYYYmmdd_HHMMSS_fff) allows lexicographical comparison
        files_to_remove = []
        
        for filename in os.listdir(self.log_dir):
            if not (filename.startswith("state_") and filename.endswith(".json")):
                continue
                
            file_ts = filename.split("_", 1)[1].split(".", 1)[0]
            # Simple string comparison works because of our timestamp format
            if file_ts > loaded_timestamp:
                files_to_remove.append(os.path.join(self.log_dir, filename))
        
        # Batch file removal
        for filepath in files_to_remove:
            try:
                os.remove(filepath)
            except OSError:
                pass  # Ignore errors during cleanup

    def save_state(self) -> None:
        """Optimized state saving with collision avoidance"""
        if not self.execution_state:
            return
            
        # Generate timestamp with microsecond precision
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
        
        # Use a counter to handle sub-microsecond collisions
        counter = 0
        while True:
            suffix = f"_{counter}" if counter > 0 else ""
            filename = f"state_{timestamp}{suffix}.json"
            filepath = os.path.join(self.log_dir, filename)
            
            if not os.path.exists(filepath):
                break
                
            counter += 1
            if counter > 100:  # Sanity check
                raise RuntimeError("Failed to generate unique state filename")
        
        # Prepare state data with metadata
        state_data = self.execution_state.to_dict()
        state_data['metadata'] = {
            'workflow_id': self.workflow_id,
            'workflow_name': self.workflow_name,
            'run_id': self.run_id,
            'save_time': timestamp
        }
        
        # Efficient file writing with atomic operation
        temp_path = f"{filepath}.tmp"
        with open(temp_path, 'w') as f:
            json.dump(state_data, f)
        os.rename(temp_path, filepath)  # Atomic operation

    async def execute_node(self, node_id: str) -> Set[str]:
        """Execute a single node and return its next node IDs."""
        node = copy.copy(self.nodes[node_id])
        
        if isinstance(node, Node):
            # Create a request_input function bound to this node
            async def request_input(prompt=None, options=None, input_type="text", request_id=None):
                # Determine the request ID (use custom ID if provided, otherwise use node_id)
                actual_request_id = request_id if request_id else node_id
                
                # Check if we already have input data for this specific request
                if hasattr(self.execution_state, 'input_data') and self.execution_state.input_data:
                    # First try the specific request_id if provided
                    node_input = self.execution_state.input_data.get(actual_request_id)
                    if node_input is not None:
                        # Clear consumed input
                        del self.execution_state.input_data[actual_request_id]
                        return node_input
                
                # Mark this node as waiting for input
                self.execution_state.node_statuses[node_id] = NodeStatus.WAITING_FOR_INPUT
                
                # Create awaiting_inputs collection if it doesn't exist
                if not hasattr(self.execution_state, 'awaiting_inputs'):
                    self.execution_state.awaiting_inputs = {}
                    
                # Store info about this waiting node
                self.execution_state.awaiting_inputs[actual_request_id] = {
                    'node_id': node_id,
                    'request_id': actual_request_id,
                    'prompt': prompt,
                    'options': options,
                    'input_type': input_type
                }
                
                # Set workflow status
                self.execution_state.workflow_status = WorkflowStatus.WAITING_FOR_INPUT
                
                # Save the current state
                if hasattr(self.execution_state, 'save_callback') and callable(self.execution_state.save_callback):
                    self.execution_state.save_callback()
                
                # Create a future for this request
                future = asyncio.Future()
                self._input_futures[actual_request_id] = future
                
                # Await the future (execution will pause here until resumed with input)
                return await future
            
            # Run the node with our request_input function
            _ = await node.run(self.execution_state, request_input)
            
        next_node_ids = node.get_next_node_ids(self.execution_state)
        
        for next_node_id in next_node_ids:
            self.execution_state.history.append({
                'timestamp': datetime.now().isoformat(),
                'from_node': node_id,
                'to_node': next_node_id
            })
        
        return next_node_ids

    async def step(self, input_data=None) -> bool:
        """Step the workflow forward with optional input data."""
        if self.execution_state.workflow_status not in {
            WorkflowStatus.NOT_STARTED,
            WorkflowStatus.RUNNING,
            WorkflowStatus.WAITING_FOR_INPUT
        }:
            return False
            
        # Handle input data if provided
        resume_tasks = []
        
        if input_data and hasattr(self.execution_state, 'awaiting_inputs'):
            # Initialize input_data dict if not exists
            if not hasattr(self.execution_state, 'input_data'):
                self.execution_state.input_data = {}
            
            for request_id, message in input_data.items():
                if request_id in self.execution_state.awaiting_inputs:
                    waiting_info = self.execution_state.awaiting_inputs[request_id]
                    node_id = waiting_info['node_id']
                    
                    # Store input for restart capability
                    self.execution_state.input_data[request_id] = message
                    
                    if request_id in self._input_futures:
                        # Handle in-process resumption via futures
                        future = self._input_futures[request_id]
                        if not future.done():
                            # Define resumption function
                            async def resume_node(node_id, future, message):
                                try:
                                    # Resolve the future to resume the coroutine
                                    future.set_result(message)
                                    
                                    # Allow coroutine to complete
                                    await asyncio.sleep(0)
                                    
                                    # Get and process next nodes
                                    node = self.nodes[node_id]
                                    next_node_ids = node.get_next_node_ids(self.execution_state)
                                    
                                    if next_node_ids:
                                        # Add successors to current_node_ids
                                        self.execution_state.current_node_ids |= next_node_ids
                                        
                                        # Add transitions to history
                                        timestamp = datetime.now().isoformat()
                                        for next_id in next_node_ids:
                                            self.execution_state.history.append({
                                                'timestamp': timestamp,
                                                'from_node': node_id,
                                                'to_node': next_id
                                            })
                                            
                                            # Mark as pending if not already tracked
                                            if next_id not in self.execution_state.node_statuses:
                                                self.execution_state.node_statuses[next_id] = NodeStatus.PENDING
                                except Exception as e:
                                    # Handle failures gracefully
                                    self.execution_state.node_statuses[node_id] = NodeStatus.FAILED
                                    logging.error(f"Error resuming node {node_id}: {str(e)}")
                            
                            # Schedule resumption
                            resume_tasks.append(asyncio.create_task(
                                resume_node(node_id, future, message)
                            ))
                        
                        # Clean up after handling
                        del self._input_futures[request_id]
                    else:
                        # Cross-process resumption via re-execution
                        self.execution_state.current_node_ids.add(node_id)
                    
                    # Request no longer waiting for input
                    del self.execution_state.awaiting_inputs[request_id]
            
            # Check if all requests for all nodes are handled
            # Group awaiting_inputs by node_id
            waiting_nodes = set()
            for info in getattr(self.execution_state, 'awaiting_inputs', {}).values():
                waiting_nodes.add(info['node_id'])
            
            # Update node statuses and workflow status
            for node_id in list(self.execution_state.node_statuses.keys()):
                if node_id not in waiting_nodes and self.execution_state.node_statuses[node_id] == NodeStatus.WAITING_FOR_INPUT:
                    # This node was waiting but all its requests are now handled
                    self.execution_state.node_statuses[node_id] = NodeStatus.ACTIVE
            
            # Update workflow status if no nodes are waiting
            if not waiting_nodes:
                self.execution_state.workflow_status = WorkflowStatus.RUNNING
        
        # Determine which nodes to execute this step
        if self.execution_state.workflow_status == WorkflowStatus.WAITING_FOR_INPUT and not input_data:
            # Only execute non-waiting nodes
            awaiting_node_ids = set(getattr(self.execution_state, 'awaiting_inputs', {}).keys())
            executable_nodes = self.execution_state.current_node_ids - awaiting_node_ids
            
            if not executable_nodes:
                # Nothing to do but wait for input
                return True
            
            current_nodes = list(executable_nodes)[:self.max_parallel_nodes]
        else:
            # Normal execution
            current_nodes = list(self.execution_state.current_node_ids)[:self.max_parallel_nodes]
        
        # Set up the save callback
        self.execution_state.save_callback = self.save_state
        
        try:
            # Wait for any resumed nodes to complete first
            if resume_tasks:
                await asyncio.gather(*resume_tasks)
            
            # Store current nodes as previous_node_ids before execution
            # Only include nodes that will actually be executed
            self.execution_state.previous_node_ids = set(current_nodes)
            
            # Execute current nodes
            if current_nodes:
                execution_tasks = [self.execute_node(node_id) for node_id in current_nodes]
                next_node_sets = await asyncio.gather(*execution_tasks)
                
                # Update current_node_ids
                self.execution_state.current_node_ids -= set(current_nodes)
                for next_nodes in next_node_sets:
                    self.execution_state.current_node_ids |= next_nodes
                    
                # Mark new nodes as pending
                for node_id in self.execution_state.current_node_ids:
                    if node_id not in self.execution_state.node_statuses:
                        self.execution_state.node_statuses[node_id] = NodeStatus.PENDING
            
            # Check if workflow is complete
            if not self.execution_state.current_node_ids and not getattr(self.execution_state, 'awaiting_inputs', {}):
                self.execution_state.workflow_status = WorkflowStatus.COMPLETED
            
            # Save current state
            self.save_state()
            
            # Return whether workflow is still active
            return self.execution_state.workflow_status in {
                WorkflowStatus.RUNNING, 
                WorkflowStatus.WAITING_FOR_INPUT
            }
        
        except Exception as e:
            # Handle workflow-level failures
            self.execution_state.workflow_status = WorkflowStatus.FAILED
            self.save_state()
            raise

    def load_state(self, filepath: str) -> None:
        """Optimized state loading that recalculates current nodes from the previous execution step"""
        with open(filepath, 'r') as f:
            state_data = json.load(f)
        
        # Load state
        self.execution_state = ExecutionState.from_dict(state_data)
        
        # Identify historical nodes and awaiting nodes for validation
        required_nodes = set()
        
        # Add historical nodes
        for entry in self.execution_state.history:
            if 'from_node' in entry:
                required_nodes.add(entry['from_node'])
            if 'to_node' in entry:
                required_nodes.add(entry['to_node'])
        
        # Add awaiting nodes (must be validated like historical nodes)
        if getattr(self.execution_state, 'awaiting_inputs', None):
            for info in self.execution_state.awaiting_inputs.values():
                if 'node_id' in info:
                    required_nodes.add(info['node_id'])
        
        # Add previous nodes (must be present in workflow)
        required_nodes.update(self.execution_state.previous_node_ids)
        
        # Fast validation using set operations
        available_nodes = set(self.nodes.keys())
        missing_nodes = required_nodes - available_nodes
        
        if missing_nodes:
            raise ValueError(
                f"Cannot load state: {len(missing_nodes)} required nodes missing. "
                f"First few: {', '.join(sorted(missing_nodes)[:3])}. "
                "Create a new run ID to continue."
            )
        
        # Clear current_node_ids and rebuild it properly
        self.execution_state.current_node_ids = set()
        
        # Add next nodes from previous execution step's nodes
        for node_id in self.execution_state.previous_node_ids:
            if node_id in self.nodes:
                node = self.nodes[node_id]
                next_nodes = node.get_next_node_ids(self.execution_state)
                self.execution_state.current_node_ids.update(next_nodes)
        
        # Update workflow status based on current_node_ids and awaiting_inputs
        waiting_exists = bool(getattr(self.execution_state, 'awaiting_inputs', None))
        
        if not self.execution_state.current_node_ids and not waiting_exists:
            self.execution_state.workflow_status = WorkflowStatus.COMPLETED
        elif waiting_exists:
            self.execution_state.workflow_status = WorkflowStatus.WAITING_FOR_INPUT
        else:
            self.execution_state.workflow_status = WorkflowStatus.RUNNING

    def get_available_timestamps(self) -> List[str]:
        """Returns a list of available timestamps in the log directory"""
        return [f.split('_')[1] for f in os.listdir(self.log_dir) if f.startswith("state_")]
        
    def get_waiting_nodes(self) -> List[Dict]:
        """Get information about nodes waiting for input."""
        if not hasattr(self.execution_state, 'awaiting_inputs'):
            return []
            
        return [
            {
                'request_id': request_id,
                'node_id': info['node_id'],
                'prompt': info['prompt'],
                'options': info['options'],
                'input_type': info['input_type']
            }
            for request_id, info in self.execution_state.awaiting_inputs.items()
        ]