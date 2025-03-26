from dataclasses import dataclass, field
import time
from typing import Callable, Dict, Any, Optional, List, Type, ClassVar, Set
from enum import Enum, auto
from datetime import datetime
import copy
import json
import asyncio
from abc import ABC, abstractmethod
import inspect
import os
from uuid import uuid4
from storage import StorageBackend, FileSystemStorage

# At the top of machine.py, before the class definitions
_NODE_REGISTRY: Dict[str, Type['Node']] = {}

class WorkflowStatus(Enum):
    """Represents the overall status of a workflow."""
    IDLE = auto()
    RUNNING = auto()
    COMPLETED = auto()
    FAILED = auto()
    WAITING_FOR_INPUT = auto()
    
class NodeStatus(str, Enum):
    """Represents the current status of a node during execution."""
    WAITING_FOR_INPUT = "waiting_for_input"
    COMPLETED = "completed"
    FAILED = "failed"

@dataclass
class ExecutionState:
    """Represents the complete state of a workflow execution."""
    shared: Dict[str, Any]
    next_node_id: Optional[str]
    workflow_status: WorkflowStatus
    node_statuses: Dict[str, NodeStatus] = field(default_factory=dict)
    awaiting_input: Optional[Dict[str, Any]] = None
    previous_node_id: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)  # Add metadata field

    def to_dict(self) -> dict:
        result = {
            'shared': self.shared,
            'next_node_id': self.next_node_id,
            'workflow_status': self.workflow_status.name,
            'node_statuses': {k: v.value for k, v in self.node_statuses.items()},
            'awaiting_input': self.awaiting_input,
            'previous_node_id': self.previous_node_id,
            'metadata': self.metadata
        }
        # Return a deep copy to ensure independence from the original state
        return copy.deepcopy(result)

    @classmethod
    def from_dict(cls, data: dict) -> 'ExecutionState':
        # Create a deep copy of the input data to ensure independence
        data = copy.deepcopy(data)
        
        # Convert string node statuses back to enum values
        node_statuses = {}
        if 'node_statuses' in data:
            node_statuses = {k: NodeStatus(v) for k, v in data['node_statuses'].items()}
            
        return cls(
            shared=data['shared'],
            next_node_id=data['next_node_id'],
            workflow_status=WorkflowStatus[data['workflow_status']],
            node_statuses=node_statuses,
            awaiting_input=data.get('awaiting_input'),
            previous_node_id=data.get('previous_node_id'),
            metadata=data.get('metadata', {})
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
        print(f"Initializing subclass: {cls.__name__}")
        if not inspect.isabstract(cls):
            _NODE_REGISTRY[cls.__name__] = cls

    @classmethod
    def get_registry(cls) -> Dict[str, Type['Node']]:
        return _NODE_REGISTRY

    @classmethod
    def clear_registry(cls) -> None:
        _NODE_REGISTRY.clear()

    def get_next_node_id(self, state: ExecutionState) -> Optional[str]:
        for transition in self.transitions.values():
            if transition.condition == "True":
                return transition.to_id
        none_transition = None
        for transition in self.transitions.values():
            if transition.condition == "None" and none_transition is None:
                none_transition = transition
            elif transition.condition != "False" and transition.condition != "None" and transition.should_transition(state):
                return transition.to_id
        return none_transition.to_id if none_transition else None

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
        prep_result = self.prepare(state.shared, request_input)
        prepared_result = await prep_result if inspect.isawaitable(prep_result) else prep_result
        
        try:
            execution_result = await self._execute_with_retry(prepared_result)
            state.node_statuses[self.id] = NodeStatus.COMPLETED
            
            cleanup_result = self.cleanup(state.shared, prepared_result, execution_result)
            return await cleanup_result if inspect.isawaitable(cleanup_result) else cleanup_result
            
        except Exception as e:
            state.node_statuses[self.id] = NodeStatus.FAILED
            raise e
            
    async def _execute_with_retry(self, prepared_result: Any) -> Any:
        """Execute with retry logic, can be extended for batch processing."""
        for self.cur_retry in range(self.max_retries):
            try:
                return await self._process_item(prepared_result)
            except Exception as e:
                if self.cur_retry == self.max_retries - 1:
                    return await self._handle_fallback(prepared_result, e)
                if self.wait > 0:
                    await asyncio.sleep(self.wait)
        return None
        
    async def _process_item(self, item: Any) -> Any:
        """Process a single item. Override this for custom item processing."""
        result = self.execute(item)
        return await result if inspect.isawaitable(result) else result
        
    async def _handle_fallback(self, prepared_result: Any, e: Exception) -> Any:
        """Handle execution failure with fallback."""
        fallback_result = self.exec_fallback(prepared_result, e)
        return await fallback_result if inspect.isawaitable(fallback_result) else fallback_result

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
    def __init__(self, from_id: str, to_id: str, condition: str = "None"):
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
            condition=data.get('condition', "None")
        )

class WorkflowEngine:
    def __init__(self, 
                 json_path: Optional[str] = None, 
                 workflow_id: Optional[str] = None,
                 start_node_id: Optional[str] = None,
                 initial_shared_state: Optional[Dict[str, Any]] = None,
                 run_id: Optional[str] = None,
                 resume_from: Optional[int] = None,
                 fork: bool = False,
                 storage_backend: Optional[StorageBackend] = None):
        
        if not json_path and not workflow_id:
            raise ValueError("Must provide json_path or workflow_id")
        
        # If workflow_id is provided but json_path is not, construct the path
        if json_path:
            workflow_id = os.path.splitext(os.path.basename(json_path))[0]
        else:
            json_path = f"{workflow_id}.json"

        if not os.path.exists(json_path):
            raise FileNotFoundError(f"No JSON file found at {json_path}")
        
        # Initialize storage backend if not provided
        self.storage = storage_backend or FileSystemStorage()
        
        with open(json_path, "r") as f:
            data = json.load(f)
        
        nodes_dict = {node_data['id']: Node.from_dict(node_data) for node_data in data['nodes']}
        
        # Add transitions
        for edge_data in data['edges']:
            transition = Transition.from_dict(edge_data)
            nodes_dict[transition.from_id].add_transition(transition)

        start_node_id = data.get('start', start_node_id)
        initial_shared_state = data.get('initial_state', initial_shared_state or {})
        
        # Validate required parameters
        if not nodes_dict or not start_node_id:
            raise ValueError("Required parameters missing (nodes, start_node_id)")
            
        # Initialize workflow properties
        self.nodes = nodes_dict
        self.start_node_id = start_node_id
        self.workflow_id = workflow_id

        if run_id:
            # Load source state for existing run
            source_data = self.storage.load_state(self.workflow_id, run_id)
            
            if not source_data:
                raise FileNotFoundError(f"No state found for run_id: {run_id}")
            
            if resume_from is None:
                resume_from = len(source_data['steps']) - 1
                
            if resume_from >= len(source_data['steps']):
                raise ValueError(f"Step {resume_from} not found. Run has {len(source_data['steps'])} steps.")

            step_data = source_data['steps'][resume_from]
            self.execution_state = ExecutionState.from_dict(step_data)
            self._validate_node_compatibility()

            if fork:
                # Fork into new branch
                self.run_id = f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_fork_{uuid4().hex[:6]}"
                self.execution_state.metadata.update({
                    'forked_from': {'run_id': run_id, 'step': resume_from},
                    'fork_time': datetime.now().isoformat(),
                    'run_id': self.run_id
                })
                self.steps = [self.execution_state.to_dict()]
            else:
                self.run_id = run_id
                # Continue in same run, purging newer steps
                self.steps = source_data['steps'][:resume_from + 1]
        else:
            self.run_id = f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_{uuid4().hex[:8]}"
            # New execution
            self.execution_state = ExecutionState(
                shared=initial_shared_state or {},
                next_node_id=start_node_id,
                workflow_status=WorkflowStatus.IDLE,
                metadata={
                    'start_time': datetime.now().isoformat(),
                    'step': 0
                }
            )
            state_dict = self.execution_state.to_dict()
            self.steps = [state_dict]

        # Save initial state
        self.storage.save_state(self.workflow_id, self.run_id, self.steps)
        self._input_futures = {}

    def save_state(self) -> None:
        """Save current execution state to the storage backend"""
        if not self.execution_state:
            return
        
        # Update metadata
        self.execution_state.metadata.update({
            'save_time': datetime.now().isoformat(),
            'step': len(self.steps)
        })
        
        # Append to steps list
        state_dict = self.execution_state.to_dict()
        self.steps.append(state_dict)
        
        # Save to storage backend
        self.storage.save_state(self.workflow_id, self.run_id, self.steps)

    async def execute_node(self, node_id: str, input_data: Optional[Dict[str, Any]] = None) -> Optional[str]:
        node = copy.copy(self.nodes[node_id])

        async def request_input(prompt=None, options=None, input_type="text", request_id=None):
            actual_request_id = request_id if request_id else node_id

            if input_data and actual_request_id in input_data:
                node_input = input_data[actual_request_id]
                if node_input is not None:
                    return node_input
            
            self.execution_state.node_statuses[node_id] = NodeStatus.WAITING_FOR_INPUT
            
            self.execution_state.awaiting_input = {
                'node_id': node_id,
                'request_id': actual_request_id,
                'prompt': prompt,
                'options': options,
                'input_type': input_type
            }
            
            self.execution_state.workflow_status = WorkflowStatus.WAITING_FOR_INPUT
            
            if hasattr(self.execution_state, 'save_callback') and callable(self.execution_state.save_callback):
                self.execution_state.save_callback()
            
            future = asyncio.Future()
            self._input_futures[actual_request_id] = future
            return await future
        
        _ = await node.run(self.execution_state, request_input)
        next_node_id = node.get_next_node_id(self.execution_state)
        
        return next_node_id
    
    async def step(self, input_data=None) -> bool:
        if (not self.execution_state.next_node_id and not self.execution_state.awaiting_input) or self.execution_state.workflow_status == WorkflowStatus.FAILED:
            return False
        
        if self.execution_state.workflow_status == WorkflowStatus.WAITING_FOR_INPUT:
            request_id = self.execution_state.awaiting_input['request_id']
            if not input_data or request_id not in input_data:
                return True

            message = input_data[request_id]
            node_id = self.execution_state.awaiting_input['node_id']
            # Clear awaiting input
            self.execution_state.awaiting_input = None
            
            # We're removing the node from waiting for input status
            # We don't mark it as "active" because we don't track future/pending nodes
            if node_id in self.execution_state.node_statuses and self.execution_state.node_statuses[node_id] == NodeStatus.WAITING_FOR_INPUT:
                del self.execution_state.node_statuses[node_id]  # Remove waiting status
            
            if request_id in self._input_futures:
                # Handle in-process resumption via futures
                future = self._input_futures[request_id]
                if not future.done():
                    # Resolve the future to resume the coroutine
                    future.set_result(message)
                    # Clean up after handling
                    del self._input_futures[request_id]
                    self.execution_state.workflow_status = WorkflowStatus.RUNNING
                    # Return immediately without further processing
                    return True
            
            # Only for cross-process resumption via re-execution
            self.execution_state.next_node_id = node_id
        
        self.execution_state.workflow_status = WorkflowStatus.RUNNING
        current_node = self.execution_state.next_node_id
        
        # Set up the save callback
        self.execution_state.save_callback = self.save_state
        
        try:            
            # Execute the current node
            next_node_id = await self.execute_node(current_node, input_data)
            # Store current node as previous_node_id before execution
            self.execution_state.previous_node_id = current_node
            
            # Update next_node_id
            self.execution_state.next_node_id = next_node_id

            self.execution_state.workflow_status = WorkflowStatus.IDLE
            
            # Check if workflow is complete
            if not self.execution_state.next_node_id and not self.execution_state.awaiting_input:
                self.execution_state.workflow_status = WorkflowStatus.COMPLETED
            
            # Save current state
            self.save_state()
            
            # Return whether workflow is still active
            return self.execution_state.workflow_status != WorkflowStatus.COMPLETED
        
        except Exception as e:
            # Handle workflow-level failures
            self.execution_state.workflow_status = WorkflowStatus.FAILED
            self.save_state()
            raise

    def _validate_node_compatibility(self) -> None:
        """Validate that required nodes exist in the current workflow"""
        # If there's a waiting node, only validate that
        if self.execution_state.awaiting_input:
            node_id = self.execution_state.awaiting_input['node_id']
            if node_id not in self.nodes:
                raise ValueError(
                    f"Cannot resume: Waiting node '{node_id}' is missing from current workflow"
                )
            return

        # Validate that either previous_node_id or next_node_id exists and is valid
        if self.execution_state.previous_node_id:
            if self.execution_state.previous_node_id not in self.nodes:
                raise ValueError(
                    f"Cannot resume: Previous node '{self.execution_state.previous_node_id}' is missing from current workflow"
                )
        elif self.execution_state.next_node_id not in self.nodes:
            raise ValueError(
                f"Cannot resume: Current node '{self.execution_state.next_node_id}' is missing from current workflow"
            )
        
        if self.execution_state.previous_node_id:
        
            prev_node = self.nodes[self.execution_state.previous_node_id]
            next_node_id = prev_node.get_next_node_id(self.execution_state)
            self.execution_state.next_node_id = next_node_id
        
    async def run(self, input_data=None):        
        # Process one step with provided input data
        if input_data and self.execution_state.awaiting_input:            
            # Call step with input data
            await self.step(input_data)
            # Give the resumed coroutine a chance to complete
            await asyncio.sleep(0)
        
        # Continue running until we need input or workflow completes
        while True:
            # Call step with no inputs to prevent accidental reuse
            continuing = await self.step(None)
            
            # Stop if workflow is completed or waiting for input
            if not continuing or self.execution_state.awaiting_input:
                break
        
        # Return the current status
        result = {
            'status': self.execution_state.workflow_status.name,
            'is_active': self.execution_state.workflow_status != WorkflowStatus.COMPLETED
        }
        
        # Add awaiting input details if relevant
        if self.execution_state.awaiting_input:
            result['awaiting_input'] = self.execution_state.awaiting_input
            
        return result