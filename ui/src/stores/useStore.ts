import { create } from 'zustand';
import { Workflow, AvailableNode, ContextMenu } from '../types/types';
import { NodeChange, EdgeChange, applyNodeChanges, applyEdgeChanges, Node, Edge } from '@xyflow/react';
import { getLayoutedElements } from '../utils/layoutUtils';
import { createMessageHandlers } from '../utils/messageHandler';
import { DebugState } from '../types/types';
import { startDebugSession, endDebugSession } from '../utils/debugActions';

export interface StoreState {
  nodes: Node[];
  edges: Edge[];
  workflows: Workflow[];
  selectedWorkflow: string | null;
  availableNodes: AvailableNode[];
  contextMenu: ContextMenu | null;
  connected: boolean;
  ws: WebSocket | null;
  setNodes: (nodes: Node[]) => void;
  setEdges: (edges: Edge[]) => void;
  onNodesChange: (changes: NodeChange[]) => void;
  onEdgesChange: (changes: EdgeChange[]) => void;
  setWorkflows: (workflows: Workflow[]) => void;
  setSelectedWorkflow: (workflowId: string | null) => void;
  setAvailableNodes: (nodes: AvailableNode[]) => void;
  setContextMenu: (menu: ContextMenu | null) => void;
  setConnected: (status: boolean) => void;
  updateFlow: () => void;
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
  workflows: [],
  selectedWorkflow: null,
  setWorkflows: (workflows) => set({ workflows }),
  setSelectedWorkflow: (workflowId: string | null) => set({ selectedWorkflow: workflowId }),

  // Available Nodes State
  availableNodes: [],
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
    const socket = new WebSocket('ws://localhost:8765');
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
  updateFlow: () => {
    const { selectedWorkflow, workflows } = get();
    if (selectedWorkflow === null) {
      set({ nodes: [], edges: [] });
      return;
    }

    const workflow = workflows.find(w => w.workflow_id === selectedWorkflow);
    if (!workflow) {
      console.error('Selected workflow not found');
      return;
    }

    const flowNodes = workflow.nodes.map(node => ({
      id: node.id.toString(),
      type: 'customNode',
      position: { x: 0, y: 0 },
      data: { 
        label: node.class,
        nodeType: node.class
      }
    }));

    const flowEdges = workflow.edges.map(edge => ({
      id: `${edge.from}-${edge.to}`,
      source: edge.from.toString(),
      target: edge.to.toString(),
      type: 'custom',
    }));

    const { nodes: layoutedNodes, edges: layoutedEdges } = getLayoutedElements(flowNodes, flowEdges);
    set({ nodes: layoutedNodes, edges: layoutedEdges });
  },

  // Debug State
  debugMode: false,
  debugRunId: null,
  debugStates: [],
  currentDebugStateIndex: -1,
  
  toggleDebugMode: (setTo?: boolean) => {
    const newDebugMode = setTo !== undefined ? setTo : !get().debugMode;
    const { debugMode, selectedWorkflow, nodes } = get();
    
    // Only take action if the state is actually changing
    if (newDebugMode === debugMode) return;
    
    set({ debugMode: newDebugMode });
    
    if (!newDebugMode) {
      set({ debugStates: [], currentDebugStateIndex: -1, debugRunId: null });
      endDebugSession();
    }
    else if (selectedWorkflow) {
      // Set all nodes to pending status when entering debug mode
      const updatedNodes = nodes.map(node => ({
        ...node,
        data: {
          ...node.data,
          status: "pending"
        }
      }));
      set({ nodes: updatedNodes });
      
      const runId = startDebugSession();
      set({ debugRunId: runId });
    }
  },
  
  setDebugRunId: (runId) => {
    set({ debugRunId: runId });
  },
  
  addDebugState: (state) => {
    set(prev => ({ 
      debugStates: [...prev.debugStates, state]
    }));
    get().goToNextDebugState();
  },
  
  setDebugStates: (states) => {
    set({ 
      debugStates: states
    });
  },
  
  goToNextDebugState: () => {
    set(prev => {
      const nextIndex = Math.min(prev.currentDebugStateIndex + 1, prev.debugStates.length - 1);
      
      // Update node statuses based on the debug state at the new index
      if (nextIndex >= 0 && prev.debugStates.length > 0) {
        const currentDebugState = prev.debugStates[nextIndex];
        const { node_statuses, current_node_ids } = currentDebugState;
        
        const updatedNodes = prev.nodes.map(node => {
          // Set default status to pending
          let status = "pending";
          
          // Apply status from node_statuses if available
          if (node_statuses && node_statuses[node.id]) {
            status = node_statuses[node.id];
          }
          
          // If the node is in current_node_ids, mark it as queued
          if (current_node_ids && current_node_ids.includes(node.id)) {
            status = "queued";
          }
          
          return {
            ...node,
            data: {
              ...node.data,
              status
            }
          };
        });
        
        return { 
          currentDebugStateIndex: nextIndex,
          nodes: updatedNodes
        };
      }
      
      return { currentDebugStateIndex: nextIndex };
    });
  },
  
  goToPreviousDebugState: () => {
    set(prev => {
      const prevIndex = Math.max(prev.currentDebugStateIndex - 1, 0);
      
      // Update node statuses based on the debug state at the new index
      if (prevIndex >= 0 && prev.debugStates.length > 0) {
        const currentDebugState = prev.debugStates[prevIndex];
        const { node_statuses, current_node_ids } = currentDebugState;
        
        const updatedNodes = prev.nodes.map(node => {
          // Set default status to pending
          let status = "pending";
          
          // Apply status from node_statuses if available
          if (node_statuses && node_statuses[node.id]) {
            status = node_statuses[node.id];
          }
          
          // If the node is in current_node_ids, mark it as queued
          if (current_node_ids && current_node_ids.includes(node.id)) {
            status = "queued";
          }
          
          return {
            ...node,
            data: {
              ...node.data,
              status
            }
          };
        });
        
        return { 
          currentDebugStateIndex: prevIndex,
          nodes: updatedNodes
        };
      }
      
      return { currentDebugStateIndex: prevIndex };
    });
  },
}));

export default useStore;