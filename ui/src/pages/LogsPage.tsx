import { Routes, Route, useParams, useNavigate } from 'react-router-dom';
import { Button } from '../components/ui/button';
import { ArrowLeft, Loader2 } from 'lucide-react';
import { useState, useEffect } from 'react';
import { fetchAllWorkflows, fetchWorkflowLogs, fetchRunLogs } from '../utils/logsApi';

// New component for displaying JSON with expand/collapse functionality
const JsonView = ({ data, initialExpanded = true, level = 0 }: { data: any, initialExpanded?: boolean, level?: number }) => {
  const [isExpanded, setIsExpanded] = useState(initialExpanded);
  
  if (data === null) return <span className="text-gray-500">null</span>;
  
  if (typeof data === 'object' && data !== null) {
    const isArray = Array.isArray(data);
    const isEmpty = Object.keys(data).length === 0;
    
    if (isEmpty) {
      return <span>{isArray ? '[]' : '{}'}</span>;
    }
    
    return (
      <div className="pl-4">
        <span 
          onClick={() => setIsExpanded(!isExpanded)} 
          className="cursor-pointer select-none text-blue-600 hover:text-blue-800"
        >
          {isExpanded ? '▼' : '►'} {isArray ? '[' : '{'} 
          {!isExpanded && (isArray 
            ? `Array(${Object.keys(data).length})` 
            : `${Object.keys(data).length} keys`
          )}
        </span>
        
        {isExpanded && (
          <div>
            {Object.entries(data).map(([key, value], i) => (
              <div key={key} className="ml-2 border-l-2 border-gray-200 pl-2">
                <span className="text-purple-600">{isArray ? '' : `"${key}": `}</span>
                {typeof value === 'object' && value !== null ? (
                  <JsonView 
                    data={value} 
                    initialExpanded={level < 1} 
                    level={level + 1} 
                  />
                ) : (
                  <span className={typeof value === 'string' ? 'text-green-600' : 'text-amber-600'}>
                    {typeof value === 'string' ? `"${value}"` : String(value)}
                  </span>
                )}
              </div>
            ))}
          </div>
        )}
        
        <span>{isArray ? ']' : '}'}</span>
      </div>
    );
  }
  
  if (typeof data === 'string') {
    return <span className="text-green-600">"{data}"</span>;
  }
  
  return <span className="text-amber-600">{String(data)}</span>;
};

// Component to display logs for a specific workflow
const WorkflowLogs = () => {
  const { workflowId } = useParams();
  const navigate = useNavigate();
  const [workflowLogs, setWorkflowLogs] = useState([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState(null);
  
  useEffect(() => {
    const getWorkflowLogs = async () => {
      if (!workflowId) return;
      
      setIsLoading(true);
      try {
        const data = await fetchWorkflowLogs(workflowId);
        setWorkflowLogs(data);
        setError(null);
      } catch (err: any) {
        setError(err.message);
      } finally {
        setIsLoading(false);
      }
    };
    
    getWorkflowLogs();
  }, [workflowId]);
  
  return (
    <div className="p-6" style={{ paddingTop: '64px' }}>
      <div className="flex justify-between items-center mb-4">
        <div className="flex items-center">
          <Button 
            variant="ghost" 
            onClick={() => navigate('/logs')}
            className="mr-2"
          >
            <ArrowLeft className="h-4 w-4" />
          </Button>
          <h2 className="text-2xl font-bold">Runs for {workflowId}</h2>
        </div>
      </div>
      <div className="border rounded-md p-4 h-[calc(100vh-140px)] overflow-auto bg-gray-50">
        {isLoading ? (
          <div className="flex justify-center items-center h-full">
            <Loader2 className="h-8 w-8 animate-spin text-gray-500" />
          </div>
        ) : error ? (
          <p className="text-red-500">Error loading logs: {error}</p>
        ) : !workflowLogs || workflowLogs.length === 0 ? (
          <p className="text-gray-500">No runs available for this workflow</p>
        ) : (
          <div className="space-y-2">
            <p className="text-gray-700 mb-4">Select a run to view its logs:</p>
            {workflowLogs.map((runId) => (
              <div 
                key={runId} 
                className="p-3 bg-white rounded shadow-sm hover:bg-blue-50 cursor-pointer transition-colors"
                onClick={() => navigate(`/logs/${workflowId}/${runId}`)}
              >
                {runId}
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};

// New component to display logs for a specific run
const RunLogs = () => {
  const { workflowId, runId } = useParams();
  const navigate = useNavigate();
  const [runLogs, setRunLogs] = useState<any>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState(null);
  
  useEffect(() => {
    const getRunLogs = async () => {
      if (!workflowId || !runId) return;
      
      setIsLoading(true);
      try {
        const data = await fetchRunLogs(workflowId, runId);
        setRunLogs(data);
        setError(null);
      } catch (err: any) {
        setError(err.message);
      } finally {
        setIsLoading(false);
      }
    };
    
    getRunLogs();
  }, [workflowId, runId]);
  
  return (
    <div className="p-6" style={{ paddingTop: '64px' }}>
      <div className="flex justify-between items-center mb-4">
        <div className="flex items-center">
          <Button 
            variant="ghost" 
            onClick={() => navigate(`/logs/${workflowId}`)}
            className="mr-2"
          >
            <ArrowLeft className="h-4 w-4" />
          </Button>
          <div>
            <h2 className="text-2xl font-bold">Logs for run ID: {runId}</h2>
            {!isLoading && !error && runLogs && 
             runLogs && 
             runLogs.steps[0] && runLogs.steps[0].metadata.forked_from && (
              <div className="text-sm text-black-500">
                Forked from run:{' '}
                <span 
                  className="text-blue-500 cursor-pointer hover:underline"
                  onClick={() => navigate(`/logs/${workflowId}/${runLogs.steps[0].metadata.forked_from}`)}
                >
                  {runLogs.steps[0].metadata.forked_from}
                </span>
                 {' '}at step {runLogs.steps[0].metadata.step}
              </div>
            )}
          </div>
        </div>
      </div>
      <div className="border rounded-md p-4 h-[calc(100vh-140px)] overflow-auto bg-gray-50">
        {isLoading ? (
          <div className="flex justify-center items-center h-full">
            <Loader2 className="h-8 w-8 animate-spin text-gray-500" />
          </div>
        ) : error ? (
          <p className="text-red-500">Error loading logs: {error}</p>
        ) : (
          <div className="font-mono text-sm">
            <JsonView data={runLogs} />
          </div>
        )}
      </div>
    </div>
  );
};

// Component to list all workflows for log selection
const LogsOverview = () => {
  const navigate = useNavigate();
  const [workflows, setWorkflows] = useState([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState(null);
  
  useEffect(() => {
    const getWorkflows = async () => {
      setIsLoading(true);
      try {
        const data = await fetchAllWorkflows();
        setWorkflows(data);
        setError(null);
      } catch (err: any) {
        setError(err.message);
      } finally {
        setIsLoading(false);
      }
    };
    
    getWorkflows();
  }, []);
  
  return (
    <div className="p-6" style={{ paddingTop: '64px' }}>
      <div className="flex justify-between items-center mb-4">
        <h2 className="text-2xl font-bold">Workflow Logs</h2>
      </div>
      <div className="border rounded-md p-4 h-[calc(100vh-140px)] overflow-auto bg-gray-50">
        {isLoading ? (
          <div className="flex justify-center items-center h-full">
            <Loader2 className="h-8 w-8 animate-spin text-gray-500" />
          </div>
        ) : error ? (
          <p className="text-red-500">Error loading workflows: {error}</p>
        ) : !workflows || workflows.length === 0 ? (
          <p className="text-gray-500">No workflows available</p>
        ) : (
          <div className="space-y-2">
            <p className="text-gray-700 mb-4">Select a workflow to view its logs:</p>
            {workflows.map((id) => (
              <div 
                key={id} 
                className="p-3 bg-white rounded shadow-sm hover:bg-blue-50 cursor-pointer transition-colors"
                onClick={() => navigate(`/logs/${id}`)}
              >
                {id}
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};

// Main LogsPage component with nested routing
const LogsPage = () => {
  return (
    <Routes>
      <Route index element={<LogsOverview />} />
      <Route path=":workflowId" element={<WorkflowLogs />} />
      <Route path=":workflowId/:runId" element={<RunLogs />} />
    </Routes>
  );
};

export default LogsPage;