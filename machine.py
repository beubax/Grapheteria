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
# At the top of machine.py, before the class definitions
_NODE_REGISTRY: Dict[str, Type['Node']] = {}

class WorkflowStatus(Enum):
    """Represents the overall status of a workflow."""
    NOT_STARTED = auto()
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
    history: List[Dict[str, Any]]
    workflow_status: WorkflowStatus
    node_statuses: Dict[str, NodeStatus] = field(default_factory=dict)
    awaiting_input: Optional[Dict[str, Any]] = None
    previous_node_id: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)  # Add metadata field
    step: int = 0  # Track the step number

    def to_dict(self) -> dict:
        result = {
            'shared': self.shared,
            'next_node_id': self.next_node_id,
            'history': self.history,
            'workflow_status': self.workflow_status.name,
            'node_statuses': {k: v.value for k, v in self.node_statuses.items()},
            'awaiting_input': self.awaiting_input,
            'previous_node_id': self.previous_node_id,
            'metadata': self.metadata,
            'step': self.step
        }
        # Return a deep copy to ensure independence from the original state
        return copy.deepcopy(result)

    @classmethod
    def from_dict(cls, data: dict) -> 'ExecutionState':
        # Convert string node statuses back to enum values
        node_statuses = {}
        if 'node_statuses' in data:
            node_statuses = {k: NodeStatus(v) for k, v in data['node_statuses'].items()}
            
        return cls(
            shared=data['shared'],
            next_node_id=data['next_node_id'],
            history=data['history'],
            workflow_status=WorkflowStatus[data['workflow_status']],
            node_statuses=node_statuses,
            awaiting_input=data.get('awaiting_input'),
            previous_node_id=data.get('previous_node_id'),
            metadata=data.get('metadata', {}),
            step=data.get('step', 0)
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

    def get_next_node_id(self, state: ExecutionState) -> Optional[str]:
        """Return only the first matching transition, or None if none match."""
        for transition in self.transitions.values():
            if transition.should_transition(state):
                return transition.to_id  # Return just the first match
        return None  # No transitions matched

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
        
        for self.cur_retry in range(self.max_retries):
            try:
                # Handle both sync and async execution automatically
                result = self.execute(prepared_result)
                execution_result = await result if inspect.isawaitable(result) else result
                
                cleanup_result = self.cleanup(state.shared, prepared_result, execution_result)
                final_result = await cleanup_result if inspect.isawaitable(cleanup_result) else cleanup_result
                state.node_statuses[self.id] = NodeStatus.COMPLETED
                return final_result
                
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
                 run_id: Optional[str] = None,
                 resume_from: Optional[int] = None,
                 fork: bool = False):
        # Load from JSON if path provided
        if json_path:
            with open(json_path, "r") as f:
                data = json.load(f)
            
            nodes_dict = {node_data['id']: Node.from_dict(node_data) for node_data in data['nodes']}
            
            # Add transitions
            for edge_data in data['edges']:
                transition = Transition.from_dict(edge_data)
                nodes_dict[transition.from_id].add_transition(transition)

            start_node_id = data['start']
            workflow_id = data['workflow_id']
            workflow_name = data.get('workflow_name')
            initial_shared_state = data.get('initial_state', {})
        
        # Validate required parameters
        if not nodes_dict or not start_node_id or not workflow_id:
            raise ValueError("Must provide json_path and (nodes_dict, start_node_id, and workflow_id)")
            
        # Initialize workflow properties
        self.nodes = nodes_dict
        self.start_node_id = start_node_id
        self.workflow_id = workflow_id
        self.workflow_name = workflow_name or workflow_id

        if run_id:
            # Load source state for existing run
            source_dir = f"logs/{self.workflow_id}/{run_id}"
            source_file = os.path.join(source_dir, "state.json")
            
            if not os.path.exists(source_file):
                raise FileNotFoundError(f"No state file found for run_id: {run_id}")
            
            with open(source_file, 'r') as f:
                source_data = json.load(f)

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
                history=[],
                workflow_status=WorkflowStatus.NOT_STARTED,
                metadata={
                    'workflow_id': self.workflow_id,
                    'run_id': self.run_id,
                    'start_time': datetime.now().isoformat()
                },
                step=0
            )
            self.steps = [self.execution_state.to_dict()]

        self.log_dir = f"logs/{self.workflow_id}/{self.run_id}"
        os.makedirs(self.log_dir, exist_ok=True)
        self.state_file = os.path.join(self.log_dir, "state.json")
        self._save_steps()
        self._input_futures = {}

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
        if not self.execution_state.next_node_id and not self.execution_state.awaiting_input:
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

            self.execution_state.workflow_status = WorkflowStatus.RUNNING
            
            if request_id in self._input_futures:
                # Handle in-process resumption via futures
                future = self._input_futures[request_id]
                if not future.done():
                    # Resolve the future to resume the coroutine
                    future.set_result(message)
                    # Clean up after handling
                    del self._input_futures[request_id]
                    
                    # Return immediately without further processing
                    # to avoid duplicate state saves, as the resumed coroutine
                    # will handle saving the state
                    return True
            
            # Only for cross-process resumption via re-execution
            self.execution_state.next_node_id = node_id
        current_node = self.execution_state.next_node_id
        
        # Set up the save callback
        self.execution_state.save_callback = self.save_state
        
        try:            
            # Execute the current node
            next_node_id = await self.execute_node(current_node, input_data)
            
            if self.execution_state.previous_node_id:
                self.execution_state.history.append({
                    'timestamp': datetime.now().isoformat(),
                    'from_node': self.execution_state.previous_node_id,
                    'to_node': current_node
                })
            # Store current node as previous_node_id before execution
            self.execution_state.previous_node_id = current_node
            
            # Update next_node_id
            self.execution_state.next_node_id = next_node_id
            
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
        
    def _save_steps(self) -> None:
        """Save all steps to a single JSON file"""
        data = {
            'workflow_id': self.workflow_id,
            'workflow_name': self.workflow_name,
            'run_id': self.run_id,
            'steps': self.steps
        }
        
        # Efficient file writing with atomic operation
        temp_path = f"{self.state_file}.tmp"
        with open(temp_path, 'w') as f:
            json.dump(data, f)
        os.rename(temp_path, self.state_file)  # Atomic operation
        
    def save_state(self) -> None:
        """Save current execution state as a new step"""
        if not self.execution_state:
            return
        
        # Increment step number
        self.execution_state.step = len(self.steps)
        
        # Update metadata
        self.execution_state.metadata.update({
            'save_time': datetime.now().isoformat()
        })
        
        # Append to steps list
        state_dict = self.execution_state.to_dict()
        self.steps.append(state_dict)  # Use deepcopy to create an independent copy
        
        # Save all steps to file
        self._save_steps()

    def get_available_steps(self) -> List[Dict[str, Any]]:
        """Returns summary information about available steps"""
        step_info = []
        
        for i, step in enumerate(self.steps):
            step_info.append({
                'step': i,
                'node_id': step.get('next_node_id'),
                'timestamp': step.get('metadata', {}).get('save_time'),
                'status': step.get('workflow_status')
            })
            
        return step_info

    def get_step_data(self, step_num: int) -> Dict[str, Any]:
        """Get detailed data for a specific step"""
        if step_num < 0 or step_num >= len(self.steps):
            raise ValueError(f"Invalid step number: {step_num}. Valid range: 0-{len(self.steps)-1}")
        
        return self.steps[step_num]
        
    def get_waiting_nodes(self) -> List[Dict]:
        """Get information about node waiting for input."""
        if not self.execution_state.awaiting_input:
            return []
        
        info = self.execution_state.awaiting_input
        return [
            {
                'request_id': info['request_id'],
                'node_id': info['node_id'],
                'prompt': info['prompt'],
                'options': info['options'],
                'input_type': info['input_type']
            }
        ]

    async def run(self, input_data=None):
        """
        Run the workflow continuously until it awaits input or completes.
        
        Args:
            input_data: Optional dict with inputs for awaiting nodes
        
        Returns:
            Dict containing workflow status and awaiting input details if any
        """
        
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