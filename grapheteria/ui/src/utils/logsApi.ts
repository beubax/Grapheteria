// API functions for fetching logs data

const API_BASE_URL = '/api'; 

export const fetchAllWorkflows = async () => {
    const response = await fetch(`${API_BASE_URL}/logs`);
    if (!response.ok) {
      throw new Error('Failed to fetch workflows');
    }
    return response.json();
  };
  
  export const fetchWorkflowLogs = async (workflowId: string    ) => {
    const response = await fetch(`${API_BASE_URL}/logs/${workflowId}`);
    if (!response.ok) {
      throw new Error(`Failed to fetch logs for workflow ${workflowId}`);
    }
    return response.json();
  };
  
  export const fetchRunLogs = async (workflowId: string, runId: string) => {
    const response = await fetch(`${API_BASE_URL}/logs/${workflowId}/${runId}`);
    if (!response.ok) {
      throw new Error(`Failed to fetch logs for run ${runId}`);
    }
    return response.json();
  };