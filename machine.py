from dataclasses import dataclass
from typing import Dict, Any, Optional, List, Type, ClassVar, Set
from enum import Enum, auto
from datetime import datetime
import time
import copy
import json
import asyncio
from abc import ABC, abstractmethod
import inspect
# At the top of machine.py, before the class definitions
_NODE_REGISTRY: Dict[str, Type['BaseNode']] = {}

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
    COMPLETED = "completed"
    FAILED = "failed"

@dataclass
class ExecutionState:
    """Represents the complete state of a workflow execution."""
    shared: Dict[str, Any]
    current_node_ids: Set[str]  # Changed to support multiple active nodes
    node_statuses: Dict[str, NodeStatus]
    history: List[Dict[str, Any]]
    workflow_status: WorkflowStatus

    def to_dict(self) -> dict:
        return {
            'shared': self.shared,
            'current_node_ids': list(self.current_node_ids),
            'node_statuses': {k: v.value for k, v in self.node_statuses.items()},
            'history': self.history,
            'workflow_status': self.workflow_status.name
        }

    @classmethod
    def from_dict(cls, data: dict) -> 'ExecutionState':
        return cls(
            shared=data['shared'],
            current_node_ids=set(data['current_node_ids']),
            node_statuses={k: NodeStatus(v) for k, v in data['node_statuses'].items()},
            history=data['history'],
            workflow_status=WorkflowStatus[data['workflow_status']]
        )

class BaseNode(ABC):
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
    def get_registry(cls) -> Dict[str, Type['BaseNode']]:
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
    def from_dict(cls, data: dict) -> 'BaseNode':
        """Factory method to create appropriate node type"""
        node_type = cls.get_registry().get(data['class'])
        if not node_type:
            raise ValueError(
                f"Unknown node type: {data['class']}. "
                f"Available types: {', '.join(sorted(cls.get_registry().keys()))}"
            )
        return node_type(id=data['id'], config=data.get('config', {}))

    async def run(self, state: ExecutionState, queue: asyncio.Queue) -> Any:
        state.node_statuses[self.id] = NodeStatus.ACTIVE
        prep_result = self.prepare(state.shared, queue)
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

    def prepare(self, shared: Dict[str, Any], queue: asyncio.Queue) -> Any:
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
    def __init__(self, nodes_dict: Dict[str, BaseNode], start_node_id: str,
                 workflow_id: str, workflow_name: str = None,
                 initial_shared_state: Dict[str, Any] = None,
                 max_parallel_nodes: int = 10):
        self.nodes = nodes_dict
        self.start_node_id = start_node_id
        self.workflow_id = workflow_id
        self.workflow_name = workflow_name or workflow_id
        self.max_parallel_nodes = max_parallel_nodes
        self.execution_state = ExecutionState(
            shared=initial_shared_state or {},
            current_node_ids={start_node_id},
            node_statuses={},
            history=[],
            workflow_status=WorkflowStatus.NOT_STARTED
        )
        self.communication_queues: Dict[str, asyncio.Queue] = {}

    @classmethod
    def from_json(cls, json_path: str):
        """Creates a workflow instance from serialized data"""
        with open(json_path, "r") as f:
            data = json.load(f)

        nodes_dict = {
            node_data['id']: BaseNode.from_dict(node_data) 
            for node_data in data['nodes']
        }
        
        for edge_data in data['edges']:
            transition = Transition.from_dict(edge_data)
            source_node = nodes_dict[transition.from_id]
            source_node.add_transition(transition)
        
        return cls(
            nodes_dict=nodes_dict,
            start_node_id=data['start'],
            workflow_id=data['workflow_id'],
            workflow_name=data.get('workflow_name'),
            initial_shared_state=data.get('initial_state', {})
        )

    async def execute_node(self, node_id: str) -> Set[str]:
        """Execute a single node and return its next node IDs."""
        node = copy.copy(self.nodes[node_id])
        queue = self.communication_queues.setdefault(node_id, asyncio.Queue())
        
        if isinstance(node, BaseNode):
            _ = await node.run(self.execution_state, queue=queue)
            
        next_node_ids = node.get_next_node_ids(self.execution_state)
        
        for next_node_id in next_node_ids:
            self.execution_state.history.append({
                'timestamp': datetime.now().isoformat(),
                'from_node': node_id,
                'to_node': next_node_id
            })
        
        return next_node_ids

    async def step(self) -> bool:
        """Executes a single step of the workflow with parallel node execution."""
        if self.execution_state.workflow_status not in {
            WorkflowStatus.NOT_STARTED,
            WorkflowStatus.RUNNING
        }:
            return False

        self.execution_state.workflow_status = WorkflowStatus.RUNNING
        
        if not self.execution_state.current_node_ids:
            self.execution_state.workflow_status = WorkflowStatus.COMPLETED
            return False

        try:
            # Create tasks for all current nodes (up to max_parallel_nodes)
            current_nodes = list(self.execution_state.current_node_ids)[:self.max_parallel_nodes]
            tasks = [self.execute_node(node_id) for node_id in current_nodes]
            
            # Execute nodes in parallel
            next_node_sets = await asyncio.gather(*tasks)
            
            # Remove completed nodes and add new nodes
            self.execution_state.current_node_ids -= set(current_nodes)
            for next_nodes in next_node_sets:
                self.execution_state.current_node_ids |= next_nodes

            # Mark remaining nodes as pending
            for node_id in self.execution_state.current_node_ids:
                if node_id not in self.execution_state.node_statuses:
                    self.execution_state.node_statuses[node_id] = NodeStatus.PENDING

            return bool(self.execution_state.current_node_ids)

        except Exception as e:
            self.execution_state.workflow_status = WorkflowStatus.FAILED
            raise

    def save_state(self, filepath: str) -> None:
        """Saves the current execution state to a file."""
        if self.execution_state:
            state_data = self.execution_state.to_dict()
            with open(filepath, 'w') as f:
                json.dump(state_data, f, indent=2)

    def load_state(self, filepath: str) -> None:
        """Loads execution state from a file."""
        with open(filepath, 'r') as f:
            state_data = json.load(f)
        self.execution_state = ExecutionState.from_dict(state_data)

# Example usage:
async def main():

    # Load workflow from JSON file
    with open("workflow.json", "r") as f:
        workflow_data = json.load(f)
    
    workflow = WorkflowEngine.from_dict(workflow_data)
    
    # Continue execution
    while True:
        has_more_steps = await workflow.step()
        print(workflow.execution_state)
        if not has_more_steps:
            break
    
    print("\nFinal state:", workflow.execution_state.to_dict())  # Changed to access execution_state directly

if __name__ == "__main__":
    asyncio.run(main())