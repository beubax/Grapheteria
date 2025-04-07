import React, { useState, useRef, useEffect } from 'react';
import useStore from '../stores/useStore';
import { stepWorkflow, startDebugSessionApi, runWorkflow } from '../utils/debugActions';
import { JSONDrawer } from './JSONDrawer';
import { Database, Loader2 } from 'lucide-react';
import { Button } from './ui/button';

const DebugDrawer: React.FC = () => {
  const { 
    toggleDebugMode,
    debugRunId,
    debugStates,
    currentDebugStateIndex,
    goToNextDebugState,
    goToPreviousDebugState,
    debugMode,
    selectedWorkflow,
  } = useStore();
  
  const [expanded, setExpanded] = useState<boolean>(false);
  const [inputData, setInputData] = useState<Record<string, any>>({});
  const [jsonDrawerOpen, setJsonDrawerOpen] = useState(false);
  const [drawerWidth, setDrawerWidth] = useState(350);
  const [isResizing, setIsResizing] = useState(false);
  const resizeRef = useRef<HTMLDivElement>(null);
  const [isStepLoading, setIsStepLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  
  // Sync drawer expanded state with global debug mode
  useEffect(() => {
    setExpanded(debugMode);
  }, [debugMode]);
  
  // Get the current debug state to display
  const currentState = debugStates[currentDebugStateIndex] || { 
    timestamp: new Date().toISOString(),
    stateVariables: { message: "No debug state available" },
    metadata: { step: "No debug state available" }
  };
  
  // Prepare input data based on awaiting input state
  const prepareInputData = () => {
    // Check if current state is awaiting input
    if (currentState.awaiting_input && currentState.awaiting_input.request_id) {
      // Create a new config with the request_id as a key but no value
      return {
        ...(Object.keys(inputData).length > 0 ? inputData : {}),
        [currentState.awaiting_input.request_id]: ""
      };
    }
    return inputData;
  };
  
  // Handle toggle debug mode
  const handleToggleDebug = async () => {
    if (!debugMode) {
      // Start debug session when turning on debug mode
      await startDebugSession();
    } else {
      // Just toggle off when turning off debug mode
      toggleDebugMode(false);
    }
  };
  
  // Start debug session with error handling
  const startDebugSession = async () => {
    if (!selectedWorkflow) {
      setError('No workflow selected');
      return;
    }
    
    setError(null);
    
    try {
      // First set debug mode to true to expand the drawer
      toggleDebugMode(true);
      
      // Then initiate the debug session with the API
      const result = await startDebugSessionApi();
      if (result?.error) {
        setError(result.error);
        // Don't turn off debug mode, just show the error
      }
    } catch (err) {
      setError('An unexpected error occurred while starting debug session');
      console.error(err);
    }
  };

  // Handle step button click
  const handleStep = async () => {  
    setIsStepLoading(true);
    setError(null); // Clear any previous errors
    try {
      // Send step message to server with inputs
      const result = await stepWorkflow(inputData);
      if (result?.error) {
        setError(result.error);
      } else {
        setInputData({});
      }
    } catch (err) {
      setError("An unexpected error occurred");
      console.error(err);
    } finally {
      setIsStepLoading(false);
    }
  };

  // Handle Run button click
  const handleRun = async () => {
    setIsStepLoading(true);
    setError(null);
    try {
      // Send run message to server with inputs
      console.log("Running workflow with input:", inputData);
      const result = await runWorkflow(inputData);
      if (result?.error) {
        setError(result.error);
      } else {
        setInputData({});
      }
    } catch (err) {
      setError("An unexpected error occurred during run");
      console.error(err);
    } finally {
      setIsStepLoading(false);
    }
  };

  // Setup resizing handlers
  const startResizing = (e: React.MouseEvent) => {
    e.preventDefault();
    setIsResizing(true);
  };

  useEffect(() => {
    const handleResize = (e: MouseEvent) => {
      if (!isResizing) return;
      
      // Calculate the new width - distance from right edge of window to mouse position
      const newWidth = window.innerWidth - e.clientX;
      
      // Limit minimum and maximum width
      if (newWidth >= 250 && newWidth <= window.innerWidth * 0.8) {
        setDrawerWidth(newWidth);
      }
    };

    const stopResizing = () => {
      setIsResizing(false);
    };

    if (isResizing) {
      document.addEventListener('mousemove', handleResize);
      document.addEventListener('mouseup', stopResizing);
    }

    return () => {
      document.removeEventListener('mousemove', handleResize);
      document.removeEventListener('mouseup', stopResizing);
    };
  }, [isResizing]);

  // Determine the error message to display, combining API errors and state errors
  let displayError: string | null = error; // Start with potential API error
  const stateErrors = currentState?.metadata?.error;
  let formattedStateErrors: string | null = null;

  // Format state errors if they exist (assuming it could be a string or array of strings)
  if (stateErrors) {
    if (Array.isArray(stateErrors) && stateErrors.length > 0) {
      formattedStateErrors = stateErrors.join(', ');
    } else if (typeof stateErrors === 'string' && stateErrors.trim() !== '') {
      formattedStateErrors = stateErrors;
    }
  }

  // Combine API error and formatted state errors
  if (formattedStateErrors) {
    if (displayError) {
      // Add a newline if both types of errors exist
      displayError = `${displayError}\n${formattedStateErrors}`;
    } else {
      displayError = formattedStateErrors;
    }
  }

  return (
    <>
      <div className={`fixed top-0 h-screen bg-[#1e1e2e] text-[#cdd6f4] flex flex-col z-50 shadow-[-2px_0_10px_rgba(0,0,0,0.2)]`}
           style={{
             right: expanded ? 0 : `-${drawerWidth}px`,
             width: `${drawerWidth}px`,
             transition: isResizing ? 'none' : 'right 0.3s ease',
           }}>
        {/* Resize handle */}
        {expanded && (
          <div 
            ref={resizeRef}
            className={`absolute left-0 h-full w-1 cursor-ew-resize hover:bg-purple-500 hover:opacity-100 transition-opacity opacity-0 ${isResizing ? 'bg-[#cba6f7]' : ''}`}
            onMouseDown={startResizing}
          />
        )}

        <div
          className="absolute -left-8 top-1/2 -translate-y-1/2 w-8 h-24 bg-[#021640] rounded-l-lg flex items-center justify-center cursor-pointer shadow-[-2px_0_5px_rgba(0,0,0,0.2)]"
          onClick={handleToggleDebug}
        >
          <span className="[writing-mode:vertical-rl] [text-orientation:mixed] text-xs text-[#cdd6f4] font-medium">
            DEBUG / RUN
          </span>
        </div>
        
        {expanded && (
          <div className="p-2 h-full flex flex-col">
            
            <div className="mb-2 flex items-center justify-between">
              <span className="text-xs">Run ID: {debugRunId || 'None'}</span>
              {isStepLoading && (
                <Loader2 className="h-4 w-4 animate-spin text-[#cba6f7]" />
              )}
            </div>
            
            {/* Error message display - updated to show API and state errors */}
            {displayError && (
              <div className="bg-[#2a2030] border border-[#f38ba8] rounded mb-2 text-xs overflow-hidden">
                <div className="bg-[#f38ba8] text-[#1e1e2e] px-2 py-1 font-medium flex items-center">
                  <svg xmlns="http://www.w3.org/2000/svg" className="h-3.5 w-3.5 mr-1" viewBox="0 0 20 20" fill="currentColor">
                    <path fillRule="evenodd" d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z" clipRule="evenodd" />
                  </svg>
                  Error
                </div>
                <div className="px-3 py-2 text-[#cdd6f4]">
                  <p className="break-words whitespace-pre-wrap">{displayError}</p>
                </div>
              </div>
            )}
            
            <div className="bg-[#313244] p-1.5 rounded mb-2 font-mono text-xs">
              <label className="block text-[#a6adc8] text-xs">Step:</label>
              <div>{currentState.metadata.step}</div>
            </div>
            
            <div className="bg-[#313244] p-1.5 rounded mb-2 flex-1 overflow-y-auto overflow-x-hidden font-mono">
              <label className="block text-[#a6adc8] text-xs">State Variables:</label>
              <pre className="m-0 whitespace-pre-wrap break-all text-xs">
                {JSON.stringify(currentState.shared, null, 2)}
              </pre>
            </div>
            
            <div className="flex justify-between mt-auto bg-[#313244] px-4 py-1.5 rounded mb-2">
              <button
                onClick={goToPreviousDebugState}
                disabled={currentDebugStateIndex <= 0 || isStepLoading}
                className={`bg-[#45475a] text-[#cdd6f4] border-none px-4 py-1 rounded text-xs ${currentDebugStateIndex <= 0 || isStepLoading ? 'opacity-50 cursor-not-allowed' : 'cursor-pointer opacity-100'}`}
              >
                ← Prev
              </button>

              <button
                onClick={handleStep}
                disabled={!debugRunId || isStepLoading}
                className={`bg-[#f38ba8] text-[#1e1e2e] border-none px-4 py-1 rounded text-xs ${!debugRunId || isStepLoading ? 'opacity-50 cursor-not-allowed' : 'cursor-pointer opacity-100'}`}
              >
                Step
              </button>

              {/* Add the Run button */}
              <button
                onClick={handleRun}
                disabled={!debugRunId || isStepLoading}
                className={`bg-[#89b4fa] text-[#1e1e2e] border-none px-4 py-1 rounded text-xs ${!debugRunId || isStepLoading ? 'opacity-50 cursor-not-allowed' : 'cursor-pointer opacity-100'}`}
              >
                {isStepLoading ? 'Running...' : 'Run >>'}
              </button>

              <button
                onClick={goToNextDebugState}
                disabled={currentDebugStateIndex >= debugStates.length - 1 || isStepLoading}
                className={`bg-[#a6e3a1] text-[#1e1e2e] border-none px-4 py-1 rounded text-xs ${currentDebugStateIndex >= debugStates.length - 1 || isStepLoading ? 'opacity-50 cursor-not-allowed' : 'cursor-pointer opacity-100'}`}
              >
                Next →
              </button>
            </div>
            
            {/* Input data section at the bottom */}
            <div className="bg-[#2a2c3d] rounded-lg p-2 shadow-md border border-[#454767]">
              <div className="flex justify-between items-center mb-1">
                <div className="text-[#cba6f7] font-medium text-xs">
                  Input Data
                </div>
                
                <Button
                  onClick={() => setJsonDrawerOpen(true)}
                  className="bg-purple-600 hover:bg-purple-500 transition-all duration-300 shadow-md text-white flex items-center gap-1 h-6 text-xs px-2"
                  size="sm"
                >
                  <Database className="h-3 w-3" />
                  <span>Configure</span>
                </Button>
              </div>
              
              {Object.keys(inputData).length > 0 ? (
                <div className="bg-[#313244] rounded p-1 max-h-[80px] overflow-auto text-[#cdd6f4] font-mono text-xs">
                  <pre className="m-0">
                    {JSON.stringify(inputData, null, 2)}
                  </pre>
                </div>
              ) : (
                <div className="bg-[#313244] rounded p-1 text-[#a6adc8] italic text-center text-xs">
                  No input data configured
                </div>
              )}
            </div>
            
            {/* JSON Drawer for debug inputs */}
            <JSONDrawer
              key={JSON.stringify(inputData) + (currentState.awaiting_input ? currentState.awaiting_input.request_id : "")}
              initialConfig={prepareInputData()}
              onSave={(config) => {
                setInputData(config);
                setJsonDrawerOpen(false);
              }}
              open={jsonDrawerOpen}
              onOpenChange={setJsonDrawerOpen}
              title="Provide Data for Waiting Node"
              variant="debug"
              keyLabel="Request_ID"
            />
          </div>
        )}
      </div>
    </>
  );
};

export default DebugDrawer;