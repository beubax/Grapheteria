import { useCallback } from 'react';
import { Connection } from '@xyflow/react';
import useStore from '../stores/useStore';

export function useGraphActions() {
  const selectedWorkflow = useStore(state => state.selectedWorkflow);
  const sendMessage = useStore(state => state.sendMessage);

  const sendWebSocketMessage = useCallback((type: string, payload: Record<string, any>) => {
    if (!selectedWorkflow) return;
    sendMessage({ type, workflow_id: selectedWorkflow, ...payload });
  }, [sendMessage, selectedWorkflow]);

  return {
    onNodeDelete: useCallback((nodeId: string) => {
      sendWebSocketMessage('node_deleted', { nodeId });
    }, [sendWebSocketMessage]),

    onEdgeDelete: useCallback((source: string, target: string) => {
      sendWebSocketMessage('edge_deleted', { from: source, to: target });
    }, [sendWebSocketMessage]),

    onEdgeCreate: useCallback((params: Connection) => {
      sendWebSocketMessage('edge_created', { from: params.source, to: params.target });
    }, [sendWebSocketMessage]),

    onNodeCreate: useCallback((nodeType: string, nodeId: string) => {
      sendWebSocketMessage('node_created', { nodeId, nodeType });
    }, [sendWebSocketMessage])
  };
}