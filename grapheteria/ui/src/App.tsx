import React, { useState } from 'react';
import { BrowserRouter as Router, Routes, Route, useNavigate, Outlet, useLocation } from 'react-router-dom';
import { Button } from './components/ui/button';
import { AlertCircle } from 'lucide-react';
import useStore from './stores/useStore';
import { useGraphActions } from './utils/graphActions';
import FlowView from './pages/FlowView';
import LogsPage from './pages/LogsPage';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter } from './components/ui/dialog';
import { Input } from './components/ui/input';
import { Label } from './components/ui/label';

// Create a layout component with the navigation bar
const AppLayout = () => {
  const {
    workflows,
    selectedWorkflow,
    connected,
    setSelectedWorkflow,
    updateFlowStructure,
    toggleDebugMode,
  } = useStore();

  const { onCreateWorkflow } = useGraphActions();
  const [newWorkflowDialogOpen, setNewWorkflowDialogOpen] = useState(false);
  const [newWorkflowName, setNewWorkflowName] = useState('');
  const [nameError, setNameError] = useState('');

  const navigate = useNavigate();
  const location = useLocation();
  const isLogsPage = location.pathname.startsWith('/logs');

  const handleWorkflowSelect = (event: React.ChangeEvent<HTMLSelectElement>) => {
    const workflowId = event.target.value;
    
    if (workflowId === 'newWorkFlowForUser') {
      // Open the new workflow dialog
      setNewWorkflowDialogOpen(true);
      return;
    }
    
    // Close debug drawer when switching workflows
    toggleDebugMode(false);
    setSelectedWorkflow(workflowId || null);
    updateFlowStructure();
  };

  const handleCreateWorkflow = () => {
    // Validate workflow name
    if (!newWorkflowName.trim()) {
      setNameError('Workflow name cannot be empty');
      return;
    }
    
    if (newWorkflowName.includes(' ')) {
      setNameError('Workflow name cannot contain spaces');
      return;
    }
    
    // Check if workflow name already exists
    if (Object.keys(workflows).includes(newWorkflowName)) {
      setNameError('Workflow name already exists');
      return;
    }
    
    // Save workflow name for later use
    const workflowNameToCreate = newWorkflowName;
    
    // Create the workflow
    onCreateWorkflow(workflowNameToCreate);
    
    // Reset and close dialog
    setNewWorkflowName('');
    setNameError('');
    setNewWorkflowDialogOpen(false);
    
    // Set up polling to check for workflow creation
    const checkInterval = 500; // Check every 500ms
    const maxWaitTime = 3000; // Wait for max 3 seconds
    let elapsedTime = 0;
    
    const waitForWorkflowCreation = () => {
      // Get the latest workflows from the store
      const currentWorkflows = useStore.getState().workflows;
      
      if (currentWorkflows[workflowNameToCreate]) {
        // Workflow is available, switch to it
        setSelectedWorkflow(workflowNameToCreate);
        updateFlowStructure();
        return;
      }
      
      if (elapsedTime >= maxWaitTime) {
        // Timeout reached, show error
        console.error(`Workflow "${workflowNameToCreate}" couldn't be created within the expected time.`);
        return;
      }
      
      // Continue waiting
      elapsedTime += checkInterval;
      setTimeout(waitForWorkflowCreation, checkInterval);
    };
    
    // Start the wait process
    setTimeout(waitForWorkflowCreation, checkInterval);
  };

  const navigateToLogs = () => {
    setSelectedWorkflow(null);
    updateFlowStructure();
    navigate('/logs');
  };

  return (
    <div style={{ width: '100vw', height: '100vh' }}>
      {/* Navigation bar */}
      <nav className="fixed top-0 left-0 right-0 bg-white shadow-sm z-10 p-3 flex items-center">
        <div className="flex-1">
          <span className="font-medium">
            {connected ? '🟢 Connected' : '🔴 Disconnected'}
          </span>
        </div>
        
        <div className="flex-1 flex justify-center items-center gap-4">
          {!isLogsPage ? (
            <>
              <div className="relative inline-block min-w-[200px]">
                <select 
                  onChange={handleWorkflowSelect} 
                  value={selectedWorkflow || ''} 
                  className="w-full p-2 rounded-md border border-gray-300 bg-white focus:outline-none focus:ring-2 focus:ring-black focus:border-transparent appearance-none pr-8"
                >
                  <option value="">Select a workflow...</option>
                  {Object.entries(workflows).map(([workflowId]) => (
                    <option key={workflowId} value={workflowId}>
                      {workflowId}
                    </option>
                  ))}
                  <option value="newWorkFlowForUser" className="text-blue-600 font-medium">+ New Workflow</option>
                </select>
                <div className="absolute inset-y-0 right-0 flex items-center px-2 pointer-events-none">
                  <svg className="w-4 h-4 text-gray-500" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                  </svg>
                </div>
              </div>
              
              <Button 
                variant="outline" 
                onClick={navigateToLogs}
                className="flex items-center gap-2 border-gray-300 hover:bg-gray-100"
              >
                <AlertCircle className="h-4 w-4" />
                Logs
              </Button>
            </>
          ) : (
            <Button 
              variant="outline" 
              onClick={() => navigate('/')}
              className="flex items-center gap-2 border-gray-300 hover:bg-gray-100"
            >
              Back to Flow Editor
            </Button>
          )}
        </div>
        
        <div className="flex-1">
          {/* Empty div to maintain spacing */}
        </div>
      </nav>
      
      {/* New Workflow Dialog */}
      <Dialog open={newWorkflowDialogOpen} onOpenChange={setNewWorkflowDialogOpen}>
        <DialogContent className="bg-white">
          <DialogHeader>
            <DialogTitle>Create New Workflow</DialogTitle>
          </DialogHeader>
          <div className="py-4">
            <Label htmlFor="workflow-name">Workflow Name</Label>
            <Input
              id="workflow-name"
              value={newWorkflowName}
              onChange={(e) => {
                setNewWorkflowName(e.target.value);
                setNameError('');
              }}
              placeholder="my_new_workflow"
              className="mt-1"
            />
            {nameError && (
              <p className="text-sm text-red-500 mt-1">{nameError}</p>
            )}
            <p className="text-sm text-gray-500 mt-1">
              Workflow name must not contain spaces.
            </p>
          </div>
          <DialogFooter>
            <Button 
              variant="outline" 
              onClick={() => {
                setNewWorkflowDialogOpen(false);
                setNewWorkflowName('');
                setNameError('');
              }}
              className="hover:bg-gray-100 cursor-pointer"
            >
              Cancel
            </Button>
            <Button 
              onClick={handleCreateWorkflow}
              className="bg-blue-500 hover:bg-blue-600 text-white cursor-pointer"
            >
              Create
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
      
      {/* Main content */}
      <Outlet />
    </div>
  );
};

// Main App component with routing
function App() {
  // Initialize WebSocket
  const initWebSocket = useStore(state => state.initWebSocket);
  
  React.useEffect(() => {
    initWebSocket();
  }, [initWebSocket]);

  return (
    <Router basename="/ui">
      <Routes>
        <Route path="/" element={<AppLayout />}>
          <Route index element={<FlowView />} />
          <Route path="logs/*" element={<LogsPage />} />
        </Route>
      </Routes>
    </Router>
  );
}

export default App;