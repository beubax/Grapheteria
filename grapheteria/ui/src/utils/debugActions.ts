import useStore from '../stores/useStore';
import axios from 'axios';

// Base API URL with the correct port
const API_BASE_URL = '/api';  // Use proxy in both dev and prod

export async function startDebugSessionApi(): Promise<{error?: string}> {
  const { selectedWorkflow, setDebugRunId, setDebugStates, goToNextDebugState } = useStore.getState();
  if (!selectedWorkflow) return { error: 'No workflow selected' };
  
  try {
    const response = await axios({
      method: 'get',
      url: `${API_BASE_URL}/workflows/create/${selectedWorkflow}`,
      headers: {
        'Content-Type': 'application/json',
        'Accept': 'application/json',
      }
    });
    
    const data = response.data;
    setDebugRunId(data.run_id);
    setDebugStates(data.execution_data.steps);
    goToNextDebugState();
    return {};

  } catch (error: unknown) {
    console.error('Error starting debug session:', error);
    // Type-safe error handling
    if (axios.isAxiosError(error) && error.response?.data?.detail) {
      return { error: error.response.data.detail };
    }
    return { error: 'Failed to start debug session' };
  }
}

export async function stepWorkflow(inputData: any): Promise<{error?: string}> {
  const { selectedWorkflow, debugRunId, currentDebugStateIndex, setDebugStates, goToNextDebugState } = useStore.getState();
  
  if (!selectedWorkflow || !debugRunId) return {};

  try {
    const response = await axios({
      method: 'post',
      url: `${API_BASE_URL}/workflows/step/${selectedWorkflow}/${debugRunId}`,
      headers: {
        'Content-Type': 'application/json',
        'Accept': 'application/json',
      },
      data: {
        resume_from: currentDebugStateIndex,
        input_data: inputData
      }
    });
    
    const data = response.data;
    console.log(data);
    setDebugStates(data.execution_data.steps);
    goToNextDebugState();
    return {};

  } catch (error: unknown) {
    console.error('Error stepping workflow:', error);
    // Type-safe error handling
    if (axios.isAxiosError(error) && error.response?.data?.detail) {
      return { error: error.response.data.detail };
    }
    return { error: 'Failed to step workflow' };
  }
}

export async function runWorkflow(inputData: any): Promise<{error?: string}> {
  const { selectedWorkflow, debugRunId, currentDebugStateIndex, setDebugStates, goToLastDebugState } = useStore.getState();
  
  if (!selectedWorkflow || !debugRunId) return {};

  try {
    const response = await axios({
      method: 'post',
      url: `${API_BASE_URL}/workflows/run/${selectedWorkflow}/${debugRunId}`,
      headers: {
        'Content-Type': 'application/json',
        'Accept': 'application/json',
      },
      data: {
        resume_from: currentDebugStateIndex,
        input_data: inputData
      }
    });
    
    const data = response.data;
    setDebugStates(data.execution_data.steps);
    goToLastDebugState();
    return {};

  } catch (error: unknown) {
    console.error('Error running workflow:', error);
    // Type-safe error handling
    if (axios.isAxiosError(error) && error.response?.data?.detail) {
      return { error: error.response.data.detail };
    }
    return { error: 'Failed to run workflow' };
  }
}
