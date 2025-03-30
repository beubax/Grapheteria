import React, { useState, useRef, useEffect } from 'react';
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
  const [drawerWidth, setDrawerWidth] = useState(350);
  const [isResizing, setIsResizing] = useState(false);
  const resizeRef = useRef<HTMLDivElement>(null);
  
  // Get the current debug state to display
  const currentState = debugStates[currentDebugStateIndex] || { 
    timestamp: new Date().toISOString(),
    stateVariables: { message: "No debug state available" },
    metadata: { step: "No debug state available" }
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

  return (
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
        className="absolute -left-10 top-1/2 -translate-y-1/2 w-10 h-30 bg-[#1e1e2e] rounded-l-lg flex items-center justify-center cursor-pointer shadow-[-2px_0_5px_rgba(0,0,0,0.2)]"
        onClick={toggleDrawer}
      >
        <span className="[writing-mode:vertical-rl] [text-orientation:mixed]">
          {expanded ? 'HIDE DEBUG' : 'DEBUG'}
        </span>
      </div>
      
      {expanded && (
        <div className="p-5 h-full flex flex-col">
          
          <div className="mb-4">
            <div className="flex justify-between items-center">
              <span>Run ID: {debugRunId || 'None'}</span>
            </div>
          </div>
          
          <div className="bg-[#313244] p-2.5 rounded mb-4 font-mono">
            <label className="block mb-1 text-[#a6adc8]">Step:</label>
            <div>{currentState.metadata.step}</div>
          </div>
          
          <div className="bg-[#313244] p-2.5 rounded mb-4 flex-1 overflow-y-auto overflow-x-hidden font-mono">
            <label className="block mb-1 text-[#a6adc8]">State Variables:</label>
            <pre className="m-0 whitespace-pre-wrap break-all">
              {JSON.stringify(currentState.shared, null, 2)}
            </pre>
          </div>
          
          <div className="flex justify-between mt-auto bg-[#313244] p-2.5 rounded mb-4"> 
            <button 
              onClick={goToPreviousDebugState}
              disabled={currentDebugStateIndex <= 0}
              className={`bg-[#45475a] text-[#cdd6f4] border-none px-4 py-2 rounded font-bold ${currentDebugStateIndex <= 0 ? 'opacity-50 cursor-not-allowed' : 'cursor-pointer opacity-100'}`}
            >
              ← Prev
            </button>
            
            <button 
              onClick={handleStep}
              disabled={!debugRunId}
              className={`bg-[#f38ba8] text-[#1e1e2e] border-none px-4 py-2 rounded font-bold ${!debugRunId ? 'opacity-50 cursor-not-allowed' : 'cursor-pointer opacity-100'}`}
            >
              Step
            </button>
            
            <button 
              onClick={goToNextDebugState}
              disabled={currentDebugStateIndex >= debugStates.length - 1}
              className={`bg-[#a6e3a1] text-[#1e1e2e] border-none px-4 py-2 rounded font-bold ${currentDebugStateIndex >= debugStates.length - 1 ? 'opacity-50 cursor-not-allowed' : 'cursor-pointer opacity-100'}`}
            >
              Next →
            </button>
          </div>
          
          {/* Input data section at the bottom */}
          <div className="bg-[#2a2c3d] rounded-lg p-3 shadow-md border border-[#454767]">
            <div className="flex justify-between items-center mb-2">
              <div className="text-[#cba6f7] font-bold text-sm">
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
              <div className="bg-[#313244] rounded p-2 max-h-[100px] overflow-auto text-[#cdd6f4] font-mono text-xs">
                <pre className="m-0">
                  {JSON.stringify(inputData, null, 2)}
                </pre>
              </div>
            ) : (
              <div className="bg-[#313244] rounded p-2 text-[#a6adc8] italic text-center">
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