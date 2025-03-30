// API functions for fetching logs data

export const fetchAllWorkflows = async () => {
    const response = await fetch('http://localhost:8765/logs');
    if (!response.ok) {
      throw new Error('Failed to fetch workflows');
    }
    return response.json();
  };
  
  export const fetchWorkflowLogs = async (workflowId: string    ) => {
    const response = await fetch(`http://localhost:8765/logs/${workflowId}`);
    if (!response.ok) {
      throw new Error(`Failed to fetch logs for workflow ${workflowId}`);
    }
    return response.json();
  };
  
  export const fetchRunLogs = async (workflowId: string, runId: string) => {
    const response = await fetch(`http://localhost:8765/logs/${workflowId}/${runId}`);
    if (!response.ok) {
      throw new Error(`Failed to fetch logs for run ${runId}`);
    }
    return response.json();
  };