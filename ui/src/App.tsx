import React from 'react';
import { BrowserRouter as Router, Routes, Route, useNavigate, Outlet, useLocation } from 'react-router-dom';
import { Button } from './components/ui/button';
import { AlertCircle } from 'lucide-react';
import useStore from './stores/useStore';
import FlowView from './pages/FlowView';
import LogsPage from './pages/LogsPage';

// Create a layout component with the navigation bar
const AppLayout = () => {
  const {
    workflows,
    selectedWorkflow,
    connected,
    setSelectedWorkflow,
    updateFlowStructure,
  } = useStore();

  const navigate = useNavigate();
  const location = useLocation();
  const isLogsPage = location.pathname.startsWith('/logs');

  const handleWorkflowSelect = (event: React.ChangeEvent<HTMLSelectElement>) => {
    const workflowId = event.target.value || null;
    setSelectedWorkflow(workflowId);
    updateFlowStructure();
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
                </select>
                <div className="absolute inset-y-0 right-0 flex items-center px-2 pointer-events-none">
                  <svg className="w-4 h-4 text-gray-500" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                  </svg>
                </div>
              </div>
              
              <Button 
                variant="outline" 
                onClick={() => navigate('/logs')}
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
    <Router>
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