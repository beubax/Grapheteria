import useStore from '../stores/useStore';
import axios from 'axios';

// Base API URL with the correct port
const API_BASE_URL = 'http://localhost:8765';

export async function startDebugSession() {
  const { selectedWorkflow, setDebugRunId, addDebugState } = useStore.getState();
  if (!selectedWorkflow) return null;
  
  try {
    const response = await axios({
      method: 'post',
      url: `${API_BASE_URL}/workflows/create`,
      headers: {
        'Content-Type': 'application/json',
        'Accept': 'application/json',
      },
      data: {
        workflow_id: selectedWorkflow
      }
    });
    
    const data = response.data;
    setDebugRunId(data.run_id);
    addDebugState(data.execution_state);

  } catch (error) {
    console.error('Error starting debug session:', error);
  }
}

export async function stepWorkflow(): Promise<void> {
  const { selectedWorkflow, debugRunId, debugStates, currentDebugStateIndex, setDebugStates, addDebugState } = useStore.getState();
  
  if (!selectedWorkflow || !debugRunId) return;

  const trimmedStates = debugStates.slice(0, currentDebugStateIndex + 1);
  setDebugStates(trimmedStates);

  try {
    const response = await axios({
      method: 'post',
      url: `${API_BASE_URL}/workflows/step`,
      headers: {
        'Content-Type': 'application/json',
        'Accept': 'application/json',
      },
      data: {
        workflow_id: selectedWorkflow,
        run_id: debugRunId,
        resume_from: currentDebugStateIndex
      }
    });
    
    const data = response.data;
    addDebugState(data.execution_state);

  } catch (error) {
    console.error('Error starting debug session:', error);
  }
}