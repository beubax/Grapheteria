import useStore from '../stores/useStore';

// Standalone functions that don't depend on React hooks
export const createDebugRunId = (): string => {
  return `debug-${Date.now()}`;
};

export function startDebugSession(): string | null {
  const { sendMessage, selectedWorkflow } = useStore.getState();
  if (!selectedWorkflow) return null;
  
  const runId = createDebugRunId();
  
  
  sendMessage({
    type: 'log_start_debug_session',
    workflow_id: selectedWorkflow,
    run_id: runId
  });
  
  return runId;
}

export function endDebugSession(): void {
  const { sendMessage } = useStore.getState();
  
  sendMessage({
    type: 'log_end_debug_session'
  });
}

export function stepWorkflow(): void {
  const { sendMessage, selectedWorkflow, debugRunId, debugStates, currentDebugStateIndex, setDebugStates } = useStore.getState();
  
  if (!selectedWorkflow || !debugRunId) return;

  // Get current timestamp from debug state
  const currentTimestamp = debugStates.length > 0 && currentDebugStateIndex >= 0 
    ? debugStates[currentDebugStateIndex].timestamp 
    : null;
  
  // If we're stepping from a previous state (not the latest),
  // remove all states that come after the current index
  if (currentTimestamp && currentDebugStateIndex < debugStates.length - 1) {
    const trimmedStates = debugStates.slice(0, currentDebugStateIndex + 1);
    setDebugStates(trimmedStates);
  }
  
  sendMessage({
    type: 'step',
    workflow_id: selectedWorkflow,
    run_id: debugRunId,
    current_timestamp: currentTimestamp
  });
}