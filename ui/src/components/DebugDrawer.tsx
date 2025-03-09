import React, { useState } from 'react';
import useStore from '../stores/useStore';
import { stepWorkflow } from '../utils/debugActions';

const DebugDrawer: React.FC = () => {
  const { 
    toggleDebugMode,
    debugRunId,
    debugStates,
    currentDebugStateIndex,
    selectedWorkflow,
    goToNextDebugState,
    goToPreviousDebugState,
  } = useStore();
  
  const [expanded, setExpanded] = useState<boolean>(false);
  
  // Get the current debug state to display
  const currentState = debugStates[currentDebugStateIndex] || { 
    timestamp: new Date().toISOString(),
    stateVariables: { message: "No debug state available" }
  };

  console.log(debugStates);
  
  // Handle opening and closing the debug drawer
  const toggleDrawer = () => {
    const newExpandedState = !expanded;
    setExpanded(newExpandedState);
    
    // Directly set debug mode to match drawer state
    toggleDebugMode(newExpandedState);
  };

  // Handle step button click
  const handleStep = () => {   
    // Send step message to server
    stepWorkflow();
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
          <h2 style={{ marginTop: 0, color: '#89b4fa' }}>Debug Panel</h2>
          
          <div style={{ marginBottom: '15px' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <span>Workflow: {selectedWorkflow || 'None'}</span>
              <span>Run ID: {debugRunId || 'None'}</span>
            </div>
            <div>
              <span>States: {debugStates.length}</span>
              <span style={{ marginLeft: '15px' }}>Current: {currentDebugStateIndex + 1}</span>
            </div>
          </div>
          
          <div className="timestamp-box" style={{
            backgroundColor: '#313244',
            padding: '10px',
            borderRadius: '5px',
            marginBottom: '15px',
            fontFamily: 'monospace'
          }}>
            <label style={{ display: 'block', marginBottom: '5px', color: '#a6adc8' }}>Timestamp:</label>
            <div>{currentState.timestamp}</div>
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
              {JSON.stringify(currentState.stateVariables, null, 2)}
            </pre>
          </div>
          
          <div className="debug-controls" style={{ 
            display: 'flex', 
            justifyContent: 'space-between', 
            marginTop: 'auto',
            backgroundColor: '#313244',
            padding: '10px',
            borderRadius: '5px'
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
        </div>
      )}
    </div>
  );
};

export default DebugDrawer;