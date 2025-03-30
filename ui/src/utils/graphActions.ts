import { useCallback } from 'react';
import { Connection } from '@xyflow/react';
import useStore from '../stores/useStore';
import { Node } from '@xyflow/react';

export function useGraphActions() {
  const selectedWorkflow = useStore(state => state.selectedWorkflow);
  const sendMessage = useStore(state => state.sendMessage);
  const debugMode = useStore(state => state.debugMode);

  const sendWebSocketMessage = useCallback((type: string, payload: Record<string, any>) => {
    if (!selectedWorkflow) return;
    sendMessage({ type, workflow_id: selectedWorkflow, ...payload });
  }, [sendMessage, selectedWorkflow]);

  return {
    onNodeDelete: useCallback((node: Node) => {
      if (debugMode && node.data?.status) {
        const protectedStatuses = ['completed', 'failed', 'waiting_for_input'];
        if (protectedStatuses.includes(node.data.status as string) || node.data.isStartNode) {
          console.log(`Cannot delete node in ${node.data.status} status during debug mode`);
          return;
        }
      }
      sendWebSocketMessage('node_deleted', { nodeId: node.id });
    }, [sendWebSocketMessage, debugMode]),

    onEdgeDelete: useCallback((source: string, target: string) => {
      sendWebSocketMessage('edge_deleted', { from: source, to: target });
    }, [sendWebSocketMessage]),

    onEdgeCreate: useCallback((params: Connection) => {
      sendWebSocketMessage('edge_created', { from: params.source, to: params.target });
    }, [sendWebSocketMessage]),

    onNodeCreate: useCallback((nodeClass: string) => {
      sendWebSocketMessage('node_created', { class:nodeClass });
    }, [sendWebSocketMessage]),
    
    onMarkAsStartNode: useCallback((nodeId: string) => {
      sendWebSocketMessage('mark_as_start_node', { nodeId: nodeId });
    }, [sendWebSocketMessage]),

    onSetEdgeCondition: useCallback((source: string, target: string, condition: string) => {
      sendWebSocketMessage('set_edge_condition', { from: source, to: target, condition: condition });
    }, [sendWebSocketMessage]),

    onSetInitialState: useCallback((initialState: Record<string, any>) => {
      sendWebSocketMessage('set_initial_state', { initialState: JSON.stringify(initialState) });
    }, [sendWebSocketMessage]),

    onSaveNodeConfig: useCallback((nodeId: string, config: Record<string, any>) => {
      sendWebSocketMessage('save_node_config', { nodeId: nodeId, config: JSON.stringify(config) });
    }, [sendWebSocketMessage]),

    onSaveNodeCode: useCallback((module: string, class_name: string, code: string) => {
      sendWebSocketMessage('save_node_code', { module: module, class: class_name, code: code });
    }, [sendWebSocketMessage])
}
}
