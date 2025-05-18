import { useState, useEffect } from 'react';
import { BrowserRouter as Router, Routes, Route, useNavigate, Outlet, useLocation } from 'react-router-dom';
import { Button } from './components/ui/button';
import { AlertCircle, Settings, Home } from 'lucide-react';
import useStore from './stores/useStore';
import FlowView from './pages/FlowView';
import LogsPage from './pages/LogsPage';
import HomePage from './pages/HomePage';
import IntegrationsPanel from './components/IntegrationsPanel';

// Create a layout component with the navigation bar
const AppLayout = () => {
  const { connected } = useStore();

  const [integrationsOpen, setIntegrationsOpen] = useState(false);

  const navigate = useNavigate();
  const location = useLocation();
  const isLogsPage = location.pathname.startsWith('/logs');
  const isHomePage = location.pathname === '/';

  const navigateToHome = () => {
    navigate('/');
  };

  const navigateToLogs = () => {
    navigate('/logs');
  };

  return (
    <div style={{ width: '100vw', height: '100vh' }}>
      {/* Navigation bar */}
      <nav className="fixed top-0 left-0 right-0 bg-white shadow-sm z-10 p-3 flex items-center">
        <div className="flex-1 flex items-center">
          <span className="font-medium ml-4">
            {connected ? '🟢 Connected' : '🔴 Disconnected'}
          </span>
        </div>
        
        <div className="flex-1 flex justify-center items-center gap-4">
          {!isHomePage && (
            <Button 
              variant="outline" 
              onClick={navigateToHome}
              className="flex items-center gap-2 border-gray-300 hover:bg-gray-100"
            >
              <Home className="h-4 w-4" />
              Home
            </Button>
          )}
          
          {!isLogsPage ? (
            <>
              <Button 
                variant="outline" 
                onClick={() => setIntegrationsOpen(true)}
                className="flex items-center gap-2 border-gray-300 hover:bg-gray-100"
              >
                <Settings className="h-4 w-4" />
                Integrations
              </Button>
              
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
            // <Button 
            //   variant="outline" 
            //   onClick={() => navigate('/')}
            //   className="flex items-center gap-2 border-gray-300 hover:bg-gray-100"
            // >
            //   Back to Home
            // </Button>
            <>  </>
          )}
        </div>
        
        <div className="flex-1 flex justify-end">
          {/* Empty div to maintain flex layout */}
        </div>
      </nav>
      
      {/* Integrations Panel Component */}
      <IntegrationsPanel 
        open={integrationsOpen}
        onOpenChange={setIntegrationsOpen}
      />
      
      {/* Main content */}
      <Outlet />
    </div>
  );
};

// Main App component with routing
function App() {
  // Initialize WebSocket
  const initWebSocket = useStore(state => state.initWebSocket);
  
  useEffect(() => {
    initWebSocket();
  }, [initWebSocket]);

  return (
    <Router basename="/ui">
      <Routes>
        <Route path="/" element={<AppLayout />}>
          <Route index element={<HomePage />} />
          <Route path="flow/:workflowId" element={<FlowView />} />
          <Route path="logs/*" element={<LogsPage />} />
        </Route>
      </Routes>
    </Router>
  );
}

export default App;