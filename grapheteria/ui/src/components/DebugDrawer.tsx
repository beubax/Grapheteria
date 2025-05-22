import React, { useState, useRef, useEffect } from 'react';
import useStore from '../stores/useStore';
import { stepWorkflow, runWorkflow } from '../utils/debugActions';
import { JSONDrawer } from './JSONDrawer';
import { Database, Loader2, MessageSquare, Bug } from 'lucide-react';
import { Button } from './ui/button';
import { Switch } from './ui/switch';
import { Input } from './ui/input';

interface DebugDrawerProps {
  debugError?: string | null;
}

const DebugDrawer: React.FC<DebugDrawerProps> = ({ debugError }) => {
  const { 
    debugRunId,
    debugStates,
    currentDebugStateIndex,
    goToNextDebugState,
    goToPreviousDebugState,
    debugMode,
  } = useStore();
  
  const [expanded, setExpanded] = useState<boolean>(false);
  const [inputData, setInputData] = useState<Record<string, any>>({});
  const [jsonDrawerOpen, setJsonDrawerOpen] = useState(false);
  const [drawerWidth, setDrawerWidth] = useState(350);
  const [isResizing, setIsResizing] = useState(false);
  const resizeRef = useRef<HTMLDivElement>(null);
  const [isStepLoading, setIsStepLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [chatMode, setChatMode] = useState<boolean>(false);
  const [chatInput, setChatInput] = useState<string>('');
  const chatContainerRef = useRef<HTMLDivElement>(null);
  const [pendingUserMessage, setPendingUserMessage] = useState<string | null>(null);
  
  // Sync drawer expanded state with global debug mode
  useEffect(() => {
    setExpanded(debugMode);
  }, [debugMode]);
  
  // Get the current debug state to display
  const currentState = debugStates[currentDebugStateIndex] || { 
    timestamp: new Date().toISOString(),
    stateVariables: { message: "No debug state available" },
    metadata: { step: "No debug state available" },
    shared: {}
  };

  // Auto-scroll chat to bottom when messages update
  useEffect(() => {
    if (chatMode && chatContainerRef.current) {
      chatContainerRef.current.scrollTop = chatContainerRef.current.scrollHeight;
    }
  }, [chatMode, currentDebugStateIndex, debugStates, pendingUserMessage]);
  
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

  // Handle run button click
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

  // Handle chat input submit
  const handleChatSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!chatInput.trim()) return;
    
    // Store the current message to display immediately
    setPendingUserMessage(chatInput);
    
    const chatData = {
      user_input: chatInput
    };
    
    setIsStepLoading(true);
    setError(null);
    
    try {
      // When in chat mode, use the same API but format the input as chat
      const result = await runWorkflow(chatData);
      if (result?.error) {
        setError(result.error);
      } else {
        // Clear pending message as workflow has updated
        setPendingUserMessage(null);
      }
      setChatInput('');
    } catch (err) {
      setError("An unexpected error occurred");
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
  let displayError: string | null = debugError || error; // Show session start error if present, else local error
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

  // Extract chat history from current state and filter to only user/assistant messages
  const chatHistory = (currentState?.shared?.chat_history || [])
    .filter((message: any) => message.role === 'assistant' || message.role === 'user');
    
  // Create a combined chat display with both history and pending message
  const combinedChatDisplay = [...chatHistory];
  
  // Add pending user message if it exists and doesn't duplicate the last message
  if (pendingUserMessage && 
      (combinedChatDisplay.length === 0 || 
       combinedChatDisplay[combinedChatDisplay.length - 1].content !== pendingUserMessage)) {
    combinedChatDisplay.push({
      role: 'user',
      content: pendingUserMessage
    });
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
          onClick={() => setExpanded((prev) => !prev)}
        >
          <span className="[writing-mode:vertical-rl] [text-orientation:mixed] text-xs text-[#cdd6f4] font-medium">
            {expanded ? 'Collapse' : 'Expand'}
          </span>
        </div>
        
        {expanded && (
          <div className="p-2 h-full flex flex-col">
            
            <div className="mb-2 flex items-center justify-between">
              <span className="text-xs">Run ID: {debugRunId || 'None'}</span>
              {isStepLoading && (
                <Loader2 className="h-4 w-4 animate-spin text-[#cba6f7]" />
              )}
              
              <div className="flex items-center space-x-2">
                <div className="flex items-center space-x-1">
                  <Bug className={`h-3.5 w-3.5 ${chatMode ? 'text-[#a6adc8]' : 'text-[#cba6f7]'}`} />
                  <MessageSquare className={`h-3.5 w-3.5 ${chatMode ? 'text-[#cba6f7]' : 'text-[#a6adc8]'}`} />
                </div>
                <Switch
                  checked={chatMode}
                  onCheckedChange={setChatMode}
                  className="ml-1"
                />
              </div>
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

            {/* Conditional rendering for chat mode vs debug mode */}
            {chatMode ? (
              // Chat Mode UI
              <>
                {/* Chat History Display */}
                <div 
                  ref={chatContainerRef}
                  className="bg-[#313244] p-2 rounded mb-2 flex-1 overflow-y-auto overflow-x-hidden"
                >
                  {combinedChatDisplay.length === 0 ? (
                    <div className="flex items-center justify-center h-full text-[#a6adc8] italic text-sm">
                      No chat messages yet
                    </div>
                  ) : (
                    <div className="flex flex-col gap-3">
                      {combinedChatDisplay.map((message: any, index: number) => (
                        <div 
                          key={index} 
                          className={`p-2 rounded-lg max-w-[85%] ${
                            message.role === 'assistant' 
                              ? 'bg-[#3a3c4e] self-start rounded-bl-none' 
                              : 'bg-[#45475a] self-end rounded-br-none'
                          }`}
                        >
                          <div className="text-xs text-[#a6adc8] mb-1">
                            {message.role === 'assistant' ? 'Assistant' : 'You'}
                          </div>
                          <div className="whitespace-pre-wrap text-sm">
                            {message.content}
                          </div>
                        </div>
                      ))}
                    </div>
                  )}
                </div>

                {/* Chat Input */}
                <form onSubmit={handleChatSubmit} className="mt-auto">
                  <div className="flex items-center gap-2">
                    <Input
                      value={chatInput}
                      onChange={(e) => setChatInput(e.target.value)}
                      placeholder="Type your message..."
                      className="flex-1 bg-[#313244] border-[#45475a] text-[#cdd6f4]"
                      disabled={isStepLoading || !debugRunId}
                    />
                    <Button 
                      type="submit"
                      className="bg-[#cba6f7] text-[#1e1e2e] hover:bg-[#b59ef1]"
                      disabled={isStepLoading || !debugRunId || !chatInput.trim()}
                    >
                      {isStepLoading ? (
                        <Loader2 className="h-4 w-4 animate-spin" />
                      ) : (
                        'Send'
                      )}
                    </Button>
                  </div>
                </form>
              </>
            ) : (
              // Debug Mode UI
              <>
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
              </>
            )}
            
            {/* JSON Drawer for debug inputs - only available in debug mode */}
            {!chatMode && (
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
            )}
          </div>
        )}
      </div>
    </>
  );
};

export default DebugDrawer;