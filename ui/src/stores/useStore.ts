import { create } from 'zustand';
import { Workflow, AvailableNode, ContextMenu } from '../types/types';
import { NodeChange, EdgeChange, applyNodeChanges, applyEdgeChanges, Node, Edge } from '@xyflow/react';
import { getLayoutedElements } from '../utils/layoutUtils';
import { createMessageHandlers } from '../utils/messageHandler';

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
}));

export default useStore;