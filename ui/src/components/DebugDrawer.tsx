import React, { useState } from 'react';
import useStore from '../stores/useStore';
import { stepWorkflow } from '../utils/debugActions';
import { JSONDrawer } from './JSONDrawer';
import { Database } from 'lucide-react';
import { Button } from './ui/button';

const DebugDrawer: React.FC = () => {
  const { 
    toggleDebugMode,
    debugRunId,
    debugStates,
    currentDebugStateIndex,
    goToNextDebugState,
    goToPreviousDebugState,
  } = useStore();
  
  const [expanded, setExpanded] = useState<boolean>(false);
  const [inputData, setInputData] = useState<Record<string, any>>({});
  const [jsonDrawerOpen, setJsonDrawerOpen] = useState(false);
  
  // Get the current debug state to display
  const currentState = debugStates[currentDebugStateIndex] || { 
    timestamp: new Date().toISOString(),
    stateVariables: { message: "No debug state available" }
  };
  
  // Handle opening and closing the debug drawer
  const toggleDrawer = () => {
    const newExpandedState = !expanded;
    setExpanded(newExpandedState);
    
    // Directly set debug mode to match drawer state
    toggleDebugMode(newExpandedState);
  };

  // Handle step button click
  const handleStep = () => {  
    // Send step message to server with inputs
    stepWorkflow(inputData);
    setInputData({});
  };

  return (
    <div className="debug-drawer" style={{
      position: 'fixed',
      right: expanded ? 0 : '-350px',
      top: 0,
      height: '100vh',
      width: '350px',
      backgroundColor: '#1e1e2e',
      color: '#cdd6f4',
      transition: 'right 0.3s ease',
      display: 'flex',
      flexDirection: 'column',
      zIndex: 1000,
      boxShadow: '-2px 0 10px rgba(0, 0, 0, 0.2)'
    }}>
      <div 
        className="debug-tab" 
        onClick={toggleDrawer}
        style={{
          position: 'absolute',
          left: '-40px',
          top: '50%',
          transform: 'translateY(-50%)',
          width: '40px',
          height: '120px',
          backgroundColor: '#1e1e2e',
          borderRadius: '8px 0 0 8px',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          cursor: 'pointer',
          boxShadow: '-2px 0 5px rgba(0, 0, 0, 0.2)'
        }}
      >
        <span style={{ writingMode: 'vertical-rl', textOrientation: 'mixed' }}>
          {expanded ? 'HIDE DEBUG' : 'DEBUG'}
        </span>
      </div>
      
      {expanded && (
        <div className="debug-content" style={{ padding: '20px', height: '100%', display: 'flex', flexDirection: 'column' }}>
          
          <div style={{ marginBottom: '15px' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <span>Run ID: {debugRunId || 'None'}</span>
            </div>
          </div>
          
          <div className="timestamp-box" style={{
            backgroundColor: '#313244',
            padding: '10px',
            borderRadius: '5px',
            marginBottom: '15px',
            fontFamily: 'monospace'
          }}>
            <label style={{ display: 'block', marginBottom: '5px', color: '#a6adc8' }}>Step:</label>
            <div>{currentState.metadata.step}</div>
          </div>
          
          <div className="state-box" style={{
            backgroundColor: '#313244',
            padding: '10px',
            borderRadius: '5px',
            marginBottom: '15px',
            flex: 1,
            overflow: 'auto',
            fontFamily: 'monospace'
          }}>
            <label style={{ display: 'block', marginBottom: '5px', color: '#a6adc8' }}>State Variables:</label>
            <pre style={{ margin: 0 }}>
              {JSON.stringify(currentState.shared, null, 2)}
            </pre>
          </div>
          
          <div className="debug-controls" style={{ 
            display: 'flex', 
            justifyContent: 'space-between', 
            marginTop: 'auto',
            backgroundColor: '#313244',
            padding: '10px',
            borderRadius: '5px',
            marginBottom: '15px'
          }}>
            <button 
              onClick={goToPreviousDebugState}
              disabled={currentDebugStateIndex <= 0}
              style={{
                backgroundColor: '#45475a',
                color: '#cdd6f4',
                border: 'none',
                padding: '8px 15px',
                borderRadius: '5px',
                cursor: currentDebugStateIndex <= 0 ? 'not-allowed' : 'pointer',
                fontWeight: 'bold',
                opacity: currentDebugStateIndex <= 0 ? 0.5 : 1
              }}
            >
              ← Prev
            </button>
            
            <button 
              onClick={handleStep}
              disabled={!debugRunId}
              style={{
                backgroundColor: '#f38ba8',
                color: '#1e1e2e',
                border: 'none',
                padding: '8px 15px',
                borderRadius: '5px',
                cursor: !debugRunId ? 'not-allowed' : 'pointer',
                fontWeight: 'bold',
                opacity: !debugRunId ? 0.5 : 1
              }}
            >
              Step
            </button>
            
            <button 
              onClick={goToNextDebugState}
              disabled={currentDebugStateIndex >= debugStates.length - 1}
              style={{
                backgroundColor: '#a6e3a1',
                color: '#1e1e2e',
                border: 'none',
                padding: '8px 15px',
                borderRadius: '5px',
                cursor: currentDebugStateIndex >= debugStates.length - 1 ? 'not-allowed' : 'pointer',
                fontWeight: 'bold',
                opacity: currentDebugStateIndex >= debugStates.length - 1 ? 0.5 : 1
              }}
            >
              Next →
            </button>
          </div>
          
          {/* Input data section at the bottom */}
          <div className="input-data-section" style={{
            backgroundColor: '#2a2c3d',
            borderRadius: '8px',
            padding: '12px',
            boxShadow: '0 -2px 10px rgba(0, 0, 0, 0.1)',
            border: '1px solid #454767'
          }}>
            <div style={{ 
              display: 'flex', 
              justifyContent: 'space-between', 
              alignItems: 'center',
              marginBottom: '8px'
            }}>
              <div style={{ 
                color: '#cba6f7', 
                fontWeight: 'bold',
                fontSize: '14px'
              }}>
                Input Data
              </div>
              
              <Button
                onClick={() => setJsonDrawerOpen(true)}
                className="bg-purple-600 hover:bg-purple-500 transition-all duration-300 shadow-md text-white flex items-center gap-1"
                size="sm"
              >
                <Database className="h-4 w-4" />
                <span>Configure</span>
              </Button>
            </div>
            
            {Object.keys(inputData).length > 0 ? (
              <div style={{
                backgroundColor: '#313244',
                borderRadius: '5px',
                padding: '8px',
                maxHeight: '100px',
                overflow: 'auto',
                color: '#cdd6f4',
                fontFamily: 'monospace',
                fontSize: '12px'
              }}>
                <pre style={{ margin: 0 }}>
                  {JSON.stringify(inputData, null, 2)}
                </pre>
              </div>
            ) : (
              <div style={{
                backgroundColor: '#313244',
                borderRadius: '5px',
                padding: '8px',
                color: '#a6adc8',
                fontStyle: 'italic',
                textAlign: 'center'
              }}>
                No input data configured
              </div>
            )}
          </div>
          
          {/* JSON Drawer for debug inputs */}
          <JSONDrawer
            initialConfig={inputData}
            onSave={(config) => {
              setInputData(config);
              setJsonDrawerOpen(false);
            }}
            open={jsonDrawerOpen}
            onOpenChange={setJsonDrawerOpen}
            title="Configure Debug Input Data"
            variant="debug"
          />
        </div>
      )}
    </div>
  );
};

export default DebugDrawer;