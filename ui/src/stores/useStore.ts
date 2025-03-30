import { create } from 'zustand';
import { Workflow, AvailableNode, ContextMenu } from '../types/types';
import { NodeChange, EdgeChange, applyNodeChanges, applyEdgeChanges, Node, Edge } from '@xyflow/react';
import { getLayoutedElements } from '../utils/layoutUtils';
import { createMessageHandlers } from '../utils/messageHandler';
import { DebugState } from '../types/types';
import { startDebugSession } from '../utils/debugActions';

export interface StoreState {
  nodes: Node[];
  edges: Edge[];
  workflows: Record<string, Workflow>;
  selectedWorkflow: string | null;
  availableNodes: AvailableNode;
  contextMenu: ContextMenu | null;
  connected: boolean;
  ws: WebSocket | null;
  setNodes: (nodes: Node[]) => void;
  setEdges: (edges: Edge[]) => void;
  onNodesChange: (changes: NodeChange[]) => void;
  onEdgesChange: (changes: EdgeChange[]) => void;
  setWorkflows: (workflows: Record<string, Workflow>) => void;
  setSelectedWorkflow: (workflowId: string | null) => void;
  setAvailableNodes: (nodes: AvailableNode) => void;
  setContextMenu: (menu: ContextMenu | null) => void;
  setConnected: (status: boolean) => void;
  updateFlowStructure: () => void;
  initWebSocket: () => void;
  sendMessage: (message: any) => void;
  debugMode: boolean;
  debugRunId: string | null;
  debugStates: DebugState[];
  currentDebugStateIndex: number;
  toggleDebugMode: (setTo?: boolean) => void;
  setDebugRunId: (runId: string | null) => void;
  addDebugState: (state: DebugState) => void;
  setDebugStates: (states: DebugState[]) => void;
  goToNextDebugState: () => void;
  goToPreviousDebugState: () => void;
  updateFlowStatus: () => void;
}

const useStore = create<StoreState>((set, get) => ({
  // Graph State
  nodes: [],
  edges: [],
  setNodes: (nodes) => set({ nodes }),
  setEdges: (edges) => set({ edges }),
  onNodesChange: (changes) => {
    set({
      nodes: applyNodeChanges(changes, get().nodes),
    });
  },
  onEdgesChange: (changes) => {
    set({
      edges: applyEdgeChanges(changes, get().edges),
    });
  },

  // Workflow State
  workflows: {},
  selectedWorkflow: null,
  setWorkflows: (workflows) => set({ workflows }),
  setSelectedWorkflow: (workflowId: string | null) => set({ selectedWorkflow: workflowId }),

  // Available Nodes State
  availableNodes: {},
  setAvailableNodes: (nodes) => set({ availableNodes: nodes }),

  // Context Menu State
  contextMenu: null,
  setContextMenu: (menu) => set({ contextMenu: menu }),

  // WebSocket Connection State
  connected: false,
  setConnected: (status) => set({ connected: status }),

  // WebSocket Instance
  ws: null,

  // WebSocket Methods
  initWebSocket: () => {
    const { ws } = get();
    
    // Check if a WebSocket connection already exists and is open/connecting
    if (ws && (ws.readyState === WebSocket.OPEN || ws.readyState === WebSocket.CONNECTING)) {
      console.log('WebSocket connection already exists');
      return;
    }
    
    // Close any existing socket before creating a new one
    if (ws) {
      ws.close();
    }
    
    const socket = new WebSocket('ws://localhost:8765/ws');
    const handleMessage = createMessageHandlers();

    socket.onopen = () => {
      console.log('Connected to WebSocket server');
      set({ connected: true });
    };

    socket.onclose = () => {
      console.log('Disconnected from WebSocket server');
      set({ connected: false });
    };

    socket.onerror = (error) => {
      console.error('WebSocket error:', error);
      set({ connected: false });
    };

    socket.onmessage = (event) => {
      const message = JSON.parse(event.data);
      handleMessage(message);
    };

    set({ ws: socket });
  },

  sendMessage: (message: any) => {
    const { ws } = get();
    if (ws && ws.readyState === WebSocket.OPEN) {
      ws.send(JSON.stringify(message));
    } else {
      console.error('WebSocket is not connected');
    }
  },

  // Actions
  updateFlowStructure: () => {
    const { selectedWorkflow, workflows, availableNodes } = get();
    if (selectedWorkflow === null) {
      set({ nodes: [], edges: [] });
      return;
    }

    const workflow = workflows[selectedWorkflow];
    if (!workflow) {
      console.error('Selected workflow not found');
      return;
    }

    const flowNodes = workflow.nodes.map(node => ({
      id: node.id.toString(),
      type: 'customNode',
      position: { x: 0, y: 0 },
      data: { 
        class: node.class,
        isStartNode: node.id === workflow.start,
        config: node.config,
        code: availableNodes[node.class] ? availableNodes[node.class][1] : null,
        module: availableNodes[node.class] ? availableNodes[node.class][0] : null,
      }
    }));

    const flowEdges = workflow.edges.map(edge => ({
      id: `${edge.from}-${edge.to}`,
      source: edge.from.toString(),
      target: edge.to.toString(),
      type: 'custom',
      data: {
        condition: edge.condition
      }
    }));

    const { nodes: layoutedNodes, edges: layoutedEdges } = getLayoutedElements(flowNodes, flowEdges);
    set({ nodes: layoutedNodes, edges: layoutedEdges });
  },

  // Debug State
  debugMode: false,
  debugRunId: null,
  debugStates: [],
  currentDebugStateIndex: -1,
  
  toggleDebugMode: async (setTo?: boolean) => {
    const newDebugMode = setTo !== undefined ? setTo : !get().debugMode;
    const { debugMode, selectedWorkflow } = get();
    
    // Only take action if the state is actually changing
    if (newDebugMode === debugMode) return;
    
    set({ debugMode: newDebugMode });
    
    if (!newDebugMode) {
      const nodes = get().nodes;
      const updatedNodes = nodes.map(node => ({
        ...node,
        data: {
          ...node.data,
        status: 'pending',
        requestDetails: null
        }
      }));
      set({ debugStates: [], nodes: updatedNodes, currentDebugStateIndex: -1, debugRunId: null });
    }
    else if (selectedWorkflow) {
      
      await startDebugSession();
    }
  },
  
  setDebugRunId: (runId) => {
    set({ debugRunId: runId });
  },
  
  addDebugState: (state) => {
    set(prev => {
      // Use step directly as the index
      const index = state.metadata.step;
      let newDebugStates = [...prev.debugStates];
      
      // Replace or add at the specific index
      newDebugStates[index] = state;
      
      return { 
        debugStates: newDebugStates
      };
    });
    
    // Let goToNextDebugState handle updating the currentDebugStateIndex
    get().goToNextDebugState();
  },
  
  setDebugStates: (states) => {
    set({ 
      debugStates: states
    });
  },
  
  updateFlowStatus: () => {
    const { debugStates, nodes, debugMode, currentDebugStateIndex } = get();
    
    // Only proceed if we are in debug mode and have a valid state index
    if (!debugMode || currentDebugStateIndex < 0 || !debugStates.length || currentDebugStateIndex >= debugStates.length) {
      return;
    }
    
    const currentDebugState = debugStates[currentDebugStateIndex];
    const { node_statuses } = currentDebugState;
    
    const updatedNodes = nodes.map(node => {
      // Set default status to pending
      let status = "pending";
      let requestDetails = null;
      
      // Apply status from node_statuses if available
      if (node_statuses && node_statuses[node.id]) {
        status = node_statuses[node.id];
      }

      if (node.id === currentDebugState.next_node_id) {
        if (status !== "waiting_for_input" && status !== "failed") {
          status = "queued";
        }
      }

      if (currentDebugState.awaiting_input && node.id === currentDebugState.awaiting_input.node_id) {
        requestDetails = currentDebugState.awaiting_input;
      }
      
      return {
        ...node,
        data: {
          ...node.data,
          status,
          requestDetails
        }
      };
    });
    
    set({ nodes: updatedNodes });
  },
  
  goToNextDebugState: () => {
    set(prev => {
      const nextIndex = Math.min(prev.currentDebugStateIndex + 1, prev.debugStates.length - 1);
      return { currentDebugStateIndex: nextIndex };
    });
    
    get().updateFlowStatus();
  },
  
  goToPreviousDebugState: () => {
    set(prev => {
      const prevIndex = Math.max(prev.currentDebugStateIndex - 1, 0);
      return { currentDebugStateIndex: prevIndex };
    });
    
    get().updateFlowStatus();
  },
}));

export default useStore;