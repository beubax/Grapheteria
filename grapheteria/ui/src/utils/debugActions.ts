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

export async function createWorkflow(workflowName: string, createDescription: string): Promise<{data?: any, error?: string}> {
  try {
    const response = await axios({
      method: 'post',
      url: `${API_BASE_URL}/workflows/create`,
      headers: {
        'Content-Type': 'application/json',
        'Accept': 'application/json',
      },
      data: {
        workflow_name: workflowName,
        create_description: createDescription
      }
    });

    const data = response.data; 
    return { data };

  } catch (error: unknown) {
    console.error('Create workflow error:', error);
    // Provide more detailed error information 
    if (axios.isAxiosError(error) && error.response) {
      return { 
        error: `Error ${error.response.status}: ${error.response.data?.detail || 'Failed to create workflow'}`
      };
    }
    return { error: 'Failed to create workflow' };
  }
}

export async function updateWorkflow(workflowId: string, updateDescription: string): Promise<{data?: any, error?: string}> {
  try {
    const response = await axios({
      method: 'post',
      url: `${API_BASE_URL}/workflows/update/${workflowId}`,
      headers: {
        'Content-Type': 'application/json',
        'Accept': 'application/json',
      },
      data: {
        update_description: updateDescription
      }
    });

    const data = response.data;
    return { data };

  } catch (error: unknown) {
    console.error('Update workflow error:', error);
    // Provide more detailed error information 
    if (axios.isAxiosError(error) && error.response) {
      return { 
        error: `Error ${error.response.status}: ${error.response.data?.detail || 'Failed to update workflow'}`
      };
    }
    return { error: 'Failed to update workflow' };
  }
}

