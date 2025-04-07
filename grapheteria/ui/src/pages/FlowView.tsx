import React, { useState } from 'react';
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
import { Settings } from 'lucide-react';
import { CodeEditor } from '../components/CodeEditor';

// Node types registration
const nodeTypes = {
  customNode: CustomNode,
};

const edgeTypes = {
  custom: CustomEdge,
};

// Main flow component
const FlowView = () => {
  const {
    nodes,
    edges,
    availableNodes,
    contextMenu,
    onNodesChange,
    onEdgesChange,
    selectedWorkflow,
    setContextMenu,
  } = useStore();

  const {
    onNodeDelete,
    onEdgeDelete,
    onEdgeCreate,
    onNodeCreate,
    onSetInitialState,
    onSaveNodeCode,
  } = useGraphActions();

  const [jsonDrawerOpen, setJsonDrawerOpen] = useState(false);
  const [customNodeEditorOpen, setCustomNodeEditorOpen] = useState(false);
  const [customNodeClassName, setCustomNodeClassName] = useState('');

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
              }}
            >
              {Object.keys(availableNodes).map((className) => (
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
      
      {selectedWorkflow && <DebugDrawer />}
      {selectedWorkflow && (
        <div className="fixed bottom-6 left-0 right-0 flex justify-center z-50">
          <Button
            onClick={() => setJsonDrawerOpen(true)}
            className="rounded-md shadow-md hover:shadow-lg transition-all duration-300 bg-black hover:bg-gray-800 text-white px-6 py-2"
            size="sm"
          >
            <Settings className="h-4 w-4 mr-2" />
            Initial State
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
      
      <CodeEditor
        initialCode={`class CustomNode(Node):
    def __init__(self, config=None):
        self.config = config or {}
    
    async def execute(self, inputs=None):
        # TODO: Implement your custom node logic here
        return {"output": "Hello from custom node!"}
`}
        onSave={(code) => {
          if (customNodeClassName.trim() === '') {
            alert('Please enter a valid class name');
            return;
          }
          
          // Save the code first
          const modulePath = 'nodes.custom';
          onSaveNodeCode(modulePath, customNodeClassName, code);
          
          // Create a loading indicator or notification here if desired
          
          // Check if the node becomes available
          const checkInterval = 500; // Check every 500ms
          const maxWaitTime = 3000; // Wait for max 3 seconds
          let elapsedTime = 0;
          
          const waitForNodeAvailability = () => {
            // Get the latest availableNodes from the store
            const currentAvailableNodes = useStore.getState().availableNodes;
            
            if (currentAvailableNodes[customNodeClassName]) {
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
        title="Create Custom Node"
        language="python"
        module="nodes.custom"
        showClassNameInput={true}
        onClassNameChange={setCustomNodeClassName}
        className={customNodeClassName}
      />
    </>
  );
};

export default FlowView;