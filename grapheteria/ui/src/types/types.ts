export interface Node {
    id: string;
    class: string;
    config: Record<string, any>;
  }
  
  export interface Edge {
    from: string | number;
    to: string | number;
    condition: string;
  }
  
  export interface Workflow {
    initial_state: Record<string, any>;
    nodes: Node[];
    edges: Edge[];
    start: string;
  }
  
  export interface AvailableNode {
    [className: string]: [string, string]; // [module, code]
  }
  
  export interface ContextMenu {
    position: { x: number; y: number };
    mousePosition: { x: number; y: number };
  }
  
  export interface WebSocketMessage {
    type: string;
    workflow_id?: string;
    workflows?: Workflow[];
    workflow?: Workflow;
    nodes?: AvailableNode;
    [key: string]: any;
  }

  export interface DebugState {
    shared: any;
    next_node_id: string;
    workflow_status: string;
    node_statuses: any;
    previous_node_id: string;
    awaiting_input: any;
    metadata: {
      step: number;
      error?: string;
    };
  }