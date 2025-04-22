from dataclasses import dataclass, field
from typing import Callable, Dict, Any, Optional, List, Type
from enum import Enum, auto
from datetime import datetime
import copy
import json
import asyncio
from abc import ABC
import inspect
import os
from uuid import uuid4
from grapheteria.utils import StorageBackend, FileSystemStorage, path_to_id, id_to_path

# At the top of machine.py, before the class definitions
_NODE_REGISTRY: Dict[str, Type["Node"]] = {}


class WorkflowStatus(Enum):
    """Represents the overall status of a workflow."""

    HEALTHY = auto()
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
            "shared": self.shared,
            "next_node_id": self.next_node_id,
            "workflow_status": self.workflow_status.name,
            "node_statuses": {k: v.value for k, v in self.node_statuses.items()},
            "awaiting_input": self.awaiting_input,
            "previous_node_id": self.previous_node_id,
            "metadata": self.metadata,
        }
        # Return a deep copy to ensure independence from the original state
        return copy.deepcopy(result)

    @classmethod
    def from_dict(cls, data: dict) -> "ExecutionState":
        # Create a deep copy of the input data to ensure independence
        data = copy.deepcopy(data)

        # Convert string node statuses back to enum values
        node_statuses = {}
        if "node_statuses" in data:
            node_statuses = {k: NodeStatus(v) for k, v in data["node_statuses"].items()}

        return cls(
            shared=data["shared"],
            next_node_id=data["next_node_id"],
            workflow_status=WorkflowStatus[data["workflow_status"]],
            node_statuses=node_statuses,
            awaiting_input=data.get("awaiting_input"),
            previous_node_id=data.get("previous_node_id"),
            metadata=data.get("metadata", {}),
        )

class ConditionSetter:
    def __init__(self, from_node: "Node", condition: str):
        self.from_node = from_node
        self.condition = condition

    def __gt__(self, to_node: "Node") -> "Node":
        self.from_node.add_edge(
            Edge(from_id=self.from_node.id, to_id=to_node.id, condition=self.condition)
        )
        return to_node


class Node(ABC):
    """Unified base class for all nodes"""

    def __init__(
        self,
        id: Optional[str] = None,
        config: Optional[Dict[str, Any]] = None,
        max_retries: int = 1,
        wait: float = 0,
    ):
        self.id = id or f"{self.__class__.__name__}_{uuid4().hex[:8]}"
        self.type = self.__class__.__name__
        self.config = config or {}
        self.edges: Dict[str, "Edge"] = {}
        self.max_retries = max_retries
        self.wait = wait
        self.cur_retry = 0

    def __init_subclass__(cls, **kwargs):
        """Auto-register nodes"""
        super().__init_subclass__(**kwargs)
        if not inspect.isabstract(cls):
            _NODE_REGISTRY[cls.__name__] = cls

    def get_next_node_id(self, state: ExecutionState) -> Optional[str]:
        for edge in self.edges.values():
            if edge.condition == "True":
                return edge.to_id
        default_edge = None
        for edge in self.edges.values():
            if edge.condition == "" and default_edge is None:
                default_edge = edge
            elif edge.should_transition(state):
                return edge.to_id
        return default_edge.to_id if default_edge else None

    def add_edge(self, edge: "Edge") -> None:
        self.edges[edge.to_id] = edge

    @classmethod
    def from_dict(cls, data: dict) -> "Node":
        """Factory method to create appropriate node type"""
        node_type = _NODE_REGISTRY.get(data["class"])
        if not node_type:
            raise ValueError(
                f"Unknown node type: {data['class']}. "
                f"Available types: {', '.join(sorted(_NODE_REGISTRY.keys()))}"
            )
        return node_type(id=data["id"], config=data.get("config", {}))

    async def run(
        self,
        state: ExecutionState,
        request_input: Callable[[str, str, str, str], Any]
    ) -> Any:
        try:
            prep_result = self.prepare(
                state.shared,
                request_input,
            )
            prepared_result = (
                await prep_result if inspect.isawaitable(prep_result) else prep_result
            )

            execution_result = await self._execute_with_retry(
                prepared_result
            )

            cleanup_result = self.cleanup(
                state.shared,
                prepared_result,
                execution_result,
            )
            _ = (
                await cleanup_result
                if inspect.isawaitable(cleanup_result)
                else cleanup_result
            )

            state.node_statuses[self.id] = NodeStatus.COMPLETED
            return

        except Exception as e:
            state.node_statuses[self.id] = NodeStatus.FAILED
            # Store exception details in metadata
            state.metadata.update({"error": type(e).__name__ + ": " + str(e)})
            raise e

    async def _execute_with_retry(
        self, prepared_result: Any
    ) -> Any:
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

    async def _process_item(self, prepared_result: Any) -> Any:
        """Process a single item."""
        result = self.execute(
            prepared_result
        )
        return await result if inspect.isawaitable(result) else result

    async def _handle_fallback(self, prepared_result: Any, e: Exception) -> Any:
        """Handle execution failure with fallback."""
        fallback_result = self.exec_fallback(
            prepared_result, e
        )
        return (
            await fallback_result
            if inspect.isawaitable(fallback_result)
            else fallback_result
        )

    def prepare(self, *args) -> Any:
        pass

    def execute(self, *args) -> Any:
        pass

    def cleanup(self, *args) -> Any:
        pass

    def exec_fallback(self, *args) -> Any:
        raise args[1]

    async def run_standalone(
        self, shared_state: Optional[Dict[str, Any]] = None
    ) -> Any:
        current_shared_state = shared_state or {}

        # Define a dummy request_input function that raises an error
        def _dummy_request_input(*args, **kwargs):
            raise NotImplementedError(
                "request_input is not available in standalone mode."
            )

        try:
            prep_result = self.prepare(
                current_shared_state, _dummy_request_input
            )
            prepared_data = (
                await prep_result if inspect.isawaitable(prep_result) else prep_result
            )

            execution_result = await self._process_item(prepared_data)

            cleanup_result = self.cleanup(
                current_shared_state,
                prepared_data,
                execution_result,
            )
            _ = (
                await cleanup_result
                if inspect.isawaitable(cleanup_result)
                else cleanup_result
            )

            return current_shared_state

        except Exception as e:
            print(f"Error running node {self.id} standalone: {type(e).__name__} - {e}")
            raise e

    def __sub__(self, condition: str) -> "ConditionSetter":
        if not isinstance(condition, str):
            raise TypeError("Condition provided via '-' must be a string.")
        return ConditionSetter(self, condition)

    def __gt__(self, other: "Node") -> "Node":
        self.add_edge(Edge(from_id=self.id, to_id=other.id))
        return other


class Edge:
    def __init__(self, from_id: str, to_id: str, condition: str = ""):
        self.from_id = from_id
        self.to_id = to_id
        self.condition = condition

    def should_transition(self, state: ExecutionState) -> bool:
        try:
            return eval(
                self.condition, {"__builtins__": __builtins__}, {"shared": state.shared}
            )
        except Exception as e:
            print(f"Error evaluating condition '{self.condition}': {str(e)}")
            return False

    @classmethod
    def from_dict(cls, data: dict) -> "Edge":
        return cls(
            from_id=data["from"], to_id=data["to"], condition=data.get("condition", "")
        )


class WorkflowEngine:
    def __init__(
        self,
        workflow_path: Optional[str] = None,
        workflow_id: Optional[str] = None,
        run_id: Optional[str] = None,
        resume_from: Optional[int] = None,
        fork: bool = False,
        storage_backend: Optional[StorageBackend] = None,
        initial_shared_state: Optional[Dict[str, Any]] = None,
        nodes: Optional[List[Node]] = None,
        start: Optional[Node] = None,
    ):
        # Initialize storage backend if not provided
        self.storage = storage_backend or FileSystemStorage()

        # Check if we're creating a workflow from code
        code_based = nodes is not None

        # For code-based workflows, we don't need workflow_path or workflow_id
        if not code_based and not workflow_path and not workflow_id:
            raise ValueError("Must provide workflow_path, workflow_id, or nodes")

        # Handle JSON-based workflow initialization
        if not code_based:
            # JSON-based initialization
            # Handle workflow path and ID conversion
            if workflow_path:
                # Normalize path and convert to posix format (forward slashes)
                workflow_id = path_to_id(workflow_path)
            else:
                # Convert ID to path - convert dots to appropriate path separators
                workflow_path = id_to_path(workflow_id)

            if not os.path.exists(workflow_path):
                raise FileNotFoundError(f"No JSON file found at {workflow_path}")

            self.workflow_id = workflow_id

            with open(workflow_path, "r") as f:
                data = json.load(f)

            if not data.get("nodes"):
                raise ValueError("No nodes found in workflow")

            nodes = data.get("nodes")

            nodes_dict = {
                node_data["id"]: Node.from_dict(node_data) for node_data in nodes
            }
            # Add edges
            for edge_data in data.get("edges", []):
                edge = Edge.from_dict(edge_data)
                nodes_dict[edge.from_id].add_edge(edge)

            start_node_id = data.get("start", None) or nodes[0]["id"]
            initial_shared_state = (
                data.get("initial_state") or initial_shared_state or {}
            )

            # Initialize workflow properties
            self.nodes = nodes_dict
            self.start_node_id = start_node_id

        else:
            if not start:
                start = nodes[0]

            # Create a workflow_id if not provided
            self.workflow_id = workflow_id or f"workflow_{uuid4().hex[:8]}"

            # Create nodes_dict from the list of nodes
            nodes_dict = {node.id: node for node in nodes}

            initial_shared_state = initial_shared_state or {}

            # Initialize workflow properties
            self.nodes = nodes_dict
            self.start_node_id = start.id

        if run_id:
            # Load source state for existing run
            self.tracking_data = self.storage.load_state(self.workflow_id, run_id)

            if not self.tracking_data:
                raise FileNotFoundError(f"No state found for run_id: {run_id}")

            if resume_from is None:
                resume_from = len(self.tracking_data["steps"]) - 1

            if resume_from >= len(self.tracking_data["steps"]):
                raise ValueError(
                    f"Step {resume_from} not found. Run has {len(self.tracking_data['steps'])} steps."
                )

            step_data = self.tracking_data["steps"][resume_from]
            self.execution_state = ExecutionState.from_dict(step_data)
            self._validate_node_compatibility()

            if fork:
                # Fork into new branch
                self.run_id = f"{datetime.now().strftime('%Y%m%d_%H%M%S_%f')[:-3]}"
                self.fork_details = {
                    "run_id": self.run_id,
                    "forked_from": run_id,
                    "fork_time": datetime.now().isoformat(),
                    "forked_step": resume_from,
                }
                self.tracking_data.update(self.fork_details)
                self.tracking_data["steps"] = [self.execution_state.to_dict()]
            else:
                self.run_id = run_id
                # Continue in same run, purging newer steps
                self.tracking_data["steps"] = self.tracking_data["steps"][
                    : resume_from + 1
                ]
            self.current_step = resume_from
        else:
            self.run_id = f"{datetime.now().strftime('%Y%m%d_%H%M%S_%f')[:-3]}"
            # New execution
            self.execution_state = ExecutionState(
                shared=initial_shared_state or {},
                next_node_id=self.start_node_id,
                workflow_status=WorkflowStatus.HEALTHY,
                metadata={"save_time": datetime.now().isoformat(), "step": 0},
            )
            state_dict = self.execution_state.to_dict()
            self.tracking_data = {
                "workflow_id": self.workflow_id,
                "run_id": self.run_id,
                "steps": [state_dict],
            }
            self.current_step = 0
        # Save initial state
        self.storage.save_state(self.workflow_id, self.run_id, self.tracking_data)
        self._input_futures = {}
        self._current_execute_task = None  # Track the current execute task

    def save_state(self) -> None:
        """Save current execution state to the storage backend"""
        if not self.execution_state:
            return

        self.current_step += 1

        # Update metadata
        self.execution_state.metadata.update(
            {"save_time": datetime.now().isoformat(), "step": self.current_step}
        )

        # Append to steps list
        state_dict = self.execution_state.to_dict()
        self.tracking_data["steps"].append(state_dict)

        # Save to storage backend
        self.storage.save_state(self.workflow_id, self.run_id, self.tracking_data)

    async def execute_node(
        self, node: Node, input_data: Optional[Dict[str, Any]] = None
    ) -> Optional[str]:
        node_id = node.id

        async def request_input(
            prompt=None, options=None, input_type="text", request_id=None
        ):
            actual_request_id = request_id if request_id else node_id
            if input_data and actual_request_id in input_data:
                node_input = input_data[actual_request_id]
                if node_input is not None:
                    return node_input

            self.execution_state.node_statuses[node_id] = NodeStatus.WAITING_FOR_INPUT

            self.execution_state.awaiting_input = {
                "node_id": node_id,
                "request_id": actual_request_id,
                "prompt": prompt,
                "options": options,
                "input_type": input_type,
            }

            self.execution_state.workflow_status = WorkflowStatus.WAITING_FOR_INPUT

            if hasattr(self.execution_state, "save_callback") and callable(
                self.execution_state.save_callback
            ):
                self.execution_state.save_callback()

            future = asyncio.Future()
            self._input_futures[actual_request_id] = future
            self.execute_event.set()
            result = await future
            return result

        await node.run(self.execution_state, request_input)
        return

    async def step(self, input_data=None) -> bool:
        if (
            not self.execution_state.next_node_id
            and not self.execution_state.awaiting_input
        ) or self.execution_state.workflow_status == WorkflowStatus.FAILED:
            return False

        if self.execution_state.workflow_status == WorkflowStatus.WAITING_FOR_INPUT:
            request_id = self.execution_state.awaiting_input["request_id"]
            if not input_data or request_id not in input_data:
                return False

            message = input_data[request_id]
            node_id = self.execution_state.awaiting_input["node_id"]
            # Clear awaiting input
            self.execution_state.awaiting_input = None
            self.execution_state.workflow_status = WorkflowStatus.HEALTHY
            # We're removing the node from waiting for input status
            # We don't mark it as "active" because we don't track future/pending nodes
            if (
                node_id in self.execution_state.node_statuses
                and self.execution_state.node_statuses[node_id]
                == NodeStatus.WAITING_FOR_INPUT
            ):
                del self.execution_state.node_statuses[node_id]  # Remove waiting status

        current_node_id = self.execution_state.next_node_id

        # Set up the save callback
        self.execution_state.save_callback = self.save_state

        try:
            self.execute_event = asyncio.Event()
            node = copy.copy(self.nodes[current_node_id])
            if self._current_execute_task:
                if not self._input_futures[request_id] or self._input_futures[request_id].done():
                    #Something went terribly wrong
                    raise Exception(f"Execution task is halted but input future for {request_id} is not set!")
                
                future = self._input_futures[request_id]
                if not future.done():
                    future.set_result(message)
                    del self._input_futures[request_id]
                    await asyncio.sleep(0)  # Let the resumed coroutine finish
            else:
                self._current_execute_task = asyncio.create_task(
                    self.execute_node(node, input_data)
                )
                event_task = asyncio.create_task(self.execute_event.wait())
                # Wait for either task to complete
                done, pending = await asyncio.wait(
                    [self._current_execute_task, event_task],
                    return_when=asyncio.FIRST_COMPLETED,
                )

                # If the event task completed, it means we're waiting for input
                if event_task in done:
                    # Don't cancel execute_task as it's waiting for input
                    # We keep self._current_execute_task for next step call
                    return False

                event_task.cancel()
                try:
                    await event_task
                except asyncio.CancelledError:
                    pass

            # If execute_task completed, we clear the reference to it
            if self._current_execute_task.done():
                # Purely for raising exceptions
                _ = self._current_execute_task.result()

                # Clear the reference to the completed task
                self._current_execute_task = None

            # Store current node as previous_node_id before execution
            self.execution_state.previous_node_id = current_node_id

            next_node_id = node.get_next_node_id(self.execution_state)

            # Update next_node_id
            self.execution_state.next_node_id = next_node_id

            # Check if workflow is complete
            if (
                not self.execution_state.next_node_id
                and not self.execution_state.awaiting_input
            ):
                self.execution_state.workflow_status = WorkflowStatus.COMPLETED
            # Save current state
            self.save_state()

            # Return whether workflow is still active
            return self.execution_state.workflow_status != WorkflowStatus.COMPLETED

        except Exception as e:
            # Handle workflow-level failures
            self.execution_state.workflow_status = WorkflowStatus.FAILED
            self.save_state()
            raise e

    def _validate_node_compatibility(self) -> None:
        """Validate that required nodes exist in the current workflow"""
        # If there's a waiting node, only validate that
        if self.execution_state.awaiting_input:
            node_id = self.execution_state.awaiting_input["node_id"]
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
        while True:
            if input_data:
                await self.step(input_data)

            continuing = await self.step()

            # Stop if workflow is completed/waiting for input or failed
            if not continuing:
                break

        return continuing
