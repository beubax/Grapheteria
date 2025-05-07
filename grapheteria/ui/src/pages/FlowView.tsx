import React, { useState, useEffect } from 'react';
import { useParams } from 'react-router-dom';
import {
  Background,
  ReactFlow,
  Controls,
} from '@xyflow/react';
import '@xyflow/react/dist/style.css';
import CustomNode from '../components/CustomNode';
import CustomConnectionLine from '../components/CustomConnectionLine';
import { useGraphActions } from '../utils/graphActions';
import useStore from '../stores/useStore';
import CustomEdge from '../components/CustomEdge';
import DebugDrawer from '../components/DebugDrawer';
import { JSONDrawer } from '../components/JSONDrawer';
import { Button } from '../components/ui/button';
import { Settings, Loader2, Sparkles } from 'lucide-react';
import { CodeEditor } from '../components/CodeEditor';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter } from '../components/ui/dialog';
import { Textarea } from '../components/ui/textarea';
import { Label } from '../components/ui/label';
import { getToolsData, capitalizeToolName } from '@/utils/toolUtils';
import IconWrapper from '@/components/ui/IconWrapper';
// Node types registration
const nodeTypes = {
  customNode: CustomNode,
};

const edgeTypes = {
  custom: CustomEdge,
};

// Main flow component
const FlowView = () => {
  const { workflowId } = useParams();
  const {
    nodes,
    edges,
    availableNodes,
    contextMenu,
    onNodesChange,
    onEdgesChange,
    selectedWorkflow,
    setSelectedWorkflow,
    setContextMenu,
    toggleDebugMode,
    updateFlowStructure,
    authenticatedTools,
    setNotificationFlag,
  } = useStore();

  const {
    onNodeDelete,
    onEdgeDelete,
    onEdgeCreate,
    onNodeCreate,
    onSetInitialState,
    onSaveNodeCode,
    onUpdateWorkflow,
  } = useGraphActions();

  const [jsonDrawerOpen, setJsonDrawerOpen] = useState(false);
  const [customNodeEditorOpen, setCustomNodeEditorOpen] = useState(false);
  const [customNodeClassName, setCustomNodeClassName] = useState('');
  const [isLoadingWorkflow, setIsLoadingWorkflow] = useState(false);
  const [aiUpdateDialogOpen, setAiUpdateDialogOpen] = useState(false);
  const [aiUpdatePrompt, setAiUpdatePrompt] = useState('');
  const [selectedIntegrations, setSelectedIntegrations] = useState<string[]>([]);
  const [isUpdatingWorkflow, setIsUpdatingWorkflow] = useState(false);

  const toggleIntegration = (integrationId: string) => {
    setSelectedIntegrations(prev => 
      prev.includes(integrationId) 
        ? prev.filter(id => id !== integrationId)
        : [...prev, integrationId]
    );
  };
  const handleAiUpdateSubmit = () => {
    if (selectedWorkflow && aiUpdatePrompt) {
      setIsUpdatingWorkflow(true);
      setNotificationFlag(false);
      
      // Call workflow update
      onUpdateWorkflow(selectedWorkflow, aiUpdatePrompt, selectedIntegrations);
      
      // Start a timeout to check for notification
      const startTime = Date.now();
      const checkInterval = 200; // Check every 200ms
      const maxWaitTime = 10000; // Wait for max 10 seconds
      
      const checkNotification = () => {
        // If notification received or timeout reached
        if (useStore.getState().notificationFlag || Date.now() - startTime >= maxWaitTime) {
          setIsUpdatingWorkflow(false);
          setAiUpdateDialogOpen(false);
          setAiUpdatePrompt('');
          setSelectedIntegrations([]);
        } else {
          // Continue checking
          setTimeout(checkNotification, checkInterval);
        }
      };
      
      // Start checking
      setTimeout(checkNotification, checkInterval);
    } else {
      setAiUpdateDialogOpen(false);
      setAiUpdatePrompt('');
      setSelectedIntegrations([]);
    }
  };

  // Set the selected workflow from URL params
  useEffect(() => {
    if (workflowId && workflowId !== selectedWorkflow) {
      // Set up polling to check for workflow creation
      setIsLoadingWorkflow(true);
      const checkInterval = 500; // Check every 500ms
      const maxWaitTime = 15000; // Wait for max 15 seconds
      let elapsedTime = 0;
      const waitForWorkflowCreation = () => {
        // Get the latest workflows from the store
        const currentWorkflows = useStore.getState().workflows;
        
        if (currentWorkflows[workflowId]) {
          toggleDebugMode(false);
          setSelectedWorkflow(workflowId);
          updateFlowStructure();
          setIsLoadingWorkflow(false);
          return;
        }
        
        if (elapsedTime >= maxWaitTime) {
          // Timeout reached, show error
          alert(`Workflow "${workflowId}" couldn't be created within the expected time.`);
          setIsLoadingWorkflow(false);
          return;
        }
        
        // Continue waiting
        elapsedTime += checkInterval;
        setTimeout(waitForWorkflowCreation, checkInterval);
      };
      
      // Start the wait process
      setTimeout(waitForWorkflowCreation, checkInterval);
    }
  }, [workflowId, selectedWorkflow, setSelectedWorkflow, updateFlowStructure, toggleDebugMode]);

  const onContextMenu = (event: React.MouseEvent<HTMLDivElement>) => {
    if (!selectedWorkflow) return;
    event.preventDefault();
    const reactFlowBounds = (event.target as HTMLDivElement).getBoundingClientRect();
    const position = {
      x: event.clientX - reactFlowBounds.left,
      y: event.clientY - reactFlowBounds.top,
    };
    
    setContextMenu({
      position,
      mousePosition: { x: event.clientX, y: event.clientY },
    });
  };

  return (
    <>
      <div style={{ width: '100%', height: '100%', paddingTop: '64px' }}>
        <ReactFlow
          nodes={nodes}
          edges={edges}
          onNodesChange={onNodesChange}
          onEdgesChange={onEdgesChange}
          onConnect={onEdgeCreate}
          onNodeDoubleClick={(_, node) => onNodeDelete(node)}
          onEdgeDoubleClick={(_, edge) => onEdgeDelete(edge.source, edge.target)}
          nodeTypes={nodeTypes}
          edgeTypes={edgeTypes}
          onContextMenu={onContextMenu}
          onPaneClick={() => setContextMenu(null)}
          fitView
          style={{ backgroundColor: "#F7F9FB" }}
          connectionLineComponent={CustomConnectionLine}
        >
          <Background />
          <Controls />
      
          {contextMenu && (
            <div
              style={{
                position: 'fixed',
                left: contextMenu.mousePosition.x,
                top: contextMenu.mousePosition.y,
                zIndex: 1000,
                backgroundColor: 'white',
                boxShadow: '0 0 10px rgba(0,0,0,0.3)',
                borderRadius: '4px',
                padding: '8px 0',
                maxHeight: '300px',
                overflowY: 'auto'
              }}
            >
              {Object.keys(availableNodes[selectedWorkflow || '']).map((className) => (
                <div
                  key={className}
                  onClick={() => {
                    onNodeCreate(className);
                    setContextMenu(null);
                  }}  
                  style={{
                    padding: '8px 16px',
                    cursor: 'pointer',
                  }}
                  className="hover:bg-gray-100"
                >
                  {className}
                </div>
              ))}
              <div
                style={{ 
                  borderTop: '1px solid #eee', 
                  margin: '4px 0' 
                }}
              />
              <div
                onClick={() => {
                  setCustomNodeClassName('');
                  setCustomNodeEditorOpen(true);
                  setContextMenu(null);
                }}
                style={{
                  padding: '8px 16px',
                  cursor: 'pointer',
                }}
                className="hover:bg-gray-100 text-blue-600 font-medium"
              >
                + Create Custom Node
              </div>
            </div>
          )}
        </ReactFlow>
      </div>
      
      {/* Loading spinner overlay */}
      {isLoadingWorkflow && (
        <div className="fixed inset-0 flex items-center justify-center bg-black/50 z-50">
          <div className="flex flex-col items-center gap-4">
            <Loader2 className="h-24 w-24 animate-spin text-white" />
            <div className="text-xl font-medium text-white">Loading workflow...</div>
          </div>
        </div>
      )}
      
      {selectedWorkflow && <DebugDrawer />}
      {selectedWorkflow && (
        <div className="fixed bottom-6 left-0 right-0 flex justify-center gap-3 z-50">
          <Button
            onClick={() => setJsonDrawerOpen(true)}
            className="rounded-md shadow-md hover:shadow-lg transition-all duration-300 bg-black hover:bg-gray-800 text-white px-6 py-2"
            size="sm"
          >
            <Settings className="h-4 w-4 mr-2" />
            Initial State
          </Button>
          
          <Button
            onClick={() => setAiUpdateDialogOpen(true)}
            className="rounded-md shadow-md hover:shadow-lg transition-all duration-300 bg-purple-600 hover:bg-purple-700 text-white px-6 py-2"
            size="sm"
          >
            <Sparkles className="h-4 w-4 mr-2" />
            AI Update
          </Button>
        </div>
      )}
      
      {selectedWorkflow && (
        <JSONDrawer 
          key={JSON.stringify(useStore.getState().workflows[selectedWorkflow].initial_state || {})}
          initialConfig={useStore.getState().workflows[selectedWorkflow].initial_state || {}} 
          onSave={onSetInitialState}
          open={jsonDrawerOpen}
          onOpenChange={setJsonDrawerOpen}
          title="Workflow Initial State"
          variant="workflow"
        />
      )}
      
      <Dialog open={aiUpdateDialogOpen} onOpenChange={(open) => !isUpdatingWorkflow && setAiUpdateDialogOpen(open)}>
        <DialogContent className="bg-white max-w-xl">
          <DialogHeader>
            <DialogTitle className="text-xl">
              {isUpdatingWorkflow ? 'Updating workflow...' : 'Update Workflow with AI'}
            </DialogTitle>
          </DialogHeader>
          
          {isUpdatingWorkflow ? (
            <div className="flex flex-col items-center justify-center py-6">
              <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-purple-600 mb-4"></div>
              <p className="text-gray-600">Updating your workflow...</p>
            </div>
          ) : (
            <div className="py-4">
              <div className="space-y-6">
                <div>
                  <Label htmlFor="ai-prompt" className="text-base font-medium block mb-2">How do you want to change your workflow?</Label>
                  <Textarea
                    id="ai-prompt"
                    value={aiUpdatePrompt}
                    onChange={(e) => setAiUpdatePrompt(e.target.value)}
                    placeholder="Add a Slack integration that sends a message when a new email arrives..."
                    className="min-h-[120px]"
                  />
                  <p className="text-sm text-gray-500 mt-2">
                    Describe in natural language how you'd like to modify or extend this workflow.
                  </p>
                </div>

                <div>
                  <Label className="text-base font-medium block mb-2">Available Integrations</Label>
                  <div className="grid grid-cols-2 gap-3 mt-2">
                    {authenticatedTools.map((integrationId) => {
                      const isSelected = selectedIntegrations.includes(integrationId);
                      const toolData = getToolsData([integrationId])[0];
                      const displayName = capitalizeToolName(integrationId);
                      
                      return (
                        <div 
                          key={integrationId}
                          onClick={() => toggleIntegration(integrationId)}
                          className={`
                            flex items-center p-3 rounded-md border cursor-pointer
                            border-gray-300 hover:border-purple-500
                            ${isSelected ? 'border-purple-500 bg-purple-50' : ''}
                          `}
                        >
                          <div className="mr-2">
                            <IconWrapper 
                              name={integrationId}
                              icon={toolData.icon}
                              color={toolData.color}
                              size="sm"
                            />
                          </div>
                          <div>
                            <div className="font-medium">{displayName}</div>
                            <div className="text-xs text-gray-500">Connected</div>
                          </div>
                          {isSelected && (
                            <div className="ml-auto text-purple-500">✓</div>
                          )}
                        </div>
                      );
                    })}
                  </div>
                  <p className="text-sm text-gray-500 mt-2">
                    Select integrations you want to use in this workflow update.
                  </p>
                </div>
              </div>
              
              <div className="flex justify-end gap-3 mt-6">
                <Button 
                  variant="outline"
                  onClick={() => setAiUpdateDialogOpen(false)}
                  className="hover:bg-gray-100"
                >
                  Cancel
                </Button>
                <Button 
                  onClick={handleAiUpdateSubmit}
                  className="bg-purple-600 hover:bg-purple-700 text-white"
                  disabled={!aiUpdatePrompt.trim()}
                >
                  <Sparkles className="h-4 w-4 mr-2" />
                  Generate Update
                </Button>
              </div>
            </div>
          )}
        </DialogContent>
      </Dialog>
      
      <CodeEditor
        initialCode={`# TODO: Implement your custom node logic here
def prepare(self, shared, request_input):
    pass

def execute(self, prepared_result):
    pass

def cleanup(self, shared, prepared_result, execution_result):
    pass
`}
        onSave={(code) => {
          if (customNodeClassName.trim() === '') {
            alert('Please enter a valid class name');
            return;
          }
          
          if (customNodeClassName.includes(' ')) {
            alert('Class name cannot contain spaces');
            return;
          }
          
          // Format the code with proper class definition and indentation
          const formattedCode = `class ${customNodeClassName}(Node):\n${code.split('\n').map(line => '    ' + line).join('\n')}`;
          
          // Save the code first
          const modulePath = `${selectedWorkflow}.nodes`; 
          onSaveNodeCode(modulePath, customNodeClassName, formattedCode);
          
          // Create a loading indicator or notification here if desired
          
          // Check if the node becomes available
          const checkInterval = 500; // Check every 500ms
          const maxWaitTime = 3000; // Wait for max 3 seconds
          let elapsedTime = 0;
          
          const waitForNodeAvailability = () => {
            // Get the latest availableNodes from the store
            const currentAvailableNodes = useStore.getState().availableNodes;
            
            if (selectedWorkflow && currentAvailableNodes[selectedWorkflow] && 
                currentAvailableNodes[selectedWorkflow][customNodeClassName]) {
              // Node is available, create it
              onNodeCreate(customNodeClassName);
              setCustomNodeEditorOpen(false);
              return;
            }
            
            if (elapsedTime >= maxWaitTime) {
              // Timeout reached, show error
              alert(`Custom node "${customNodeClassName}" couldn't be registered. Please check your code for errors.`);
              setCustomNodeEditorOpen(false);
              return;
            }
            
            // Continue waiting
            elapsedTime += checkInterval;
            setTimeout(waitForNodeAvailability, checkInterval);
          };
          
          // Start the wait process
          setTimeout(waitForNodeAvailability, checkInterval);
        }}
        open={customNodeEditorOpen}
        onOpenChange={setCustomNodeEditorOpen}
        language="python"
        module={`${selectedWorkflow}.nodes`}
        onClassNameChange={setCustomNodeClassName}
        className={customNodeClassName}
        classNameEditable={true}
      />
    </>
  );
};

export default FlowView;