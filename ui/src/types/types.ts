export interface Node {
    id: string;
    class: string;
  }
  
  export interface Edge {
    from: string | number;
    to: string | number;
  }
  
  export interface Workflow {
    workflow_id: string;
    workflow_name?: string;
    nodes: Node[];
    edges: Edge[];
  }
  
  export interface AvailableNode {
    name: string;
    type: string;
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
    nodes?: AvailableNode[];
    [key: string]: any;
  }

  export interface DebugState {
    timestamp: string;
    stateVariables: any;
    node_statuses: any;
    current_node_ids: string[];
  }