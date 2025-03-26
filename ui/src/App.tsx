import React, { useState } from 'react';
import {
    Background,
    ReactFlow,
    Controls,
  } from '@xyflow/react';
import '@xyflow/react/dist/style.css';
import CustomNode from './components/CustomNode';
import CustomConnectionLine from './components/CustomConnectionLine';
import { useGraphActions } from './utils/graphActions';
import useStore from './stores/useStore';
import CustomEdge from './components/CustomEdge';
import DebugDrawer from './components/DebugDrawer';
import { JSONDrawer } from './components/JSONDrawer';
import { Button } from './components/ui/button';
import { Settings } from 'lucide-react';

// Node types registration

const nodeTypes = {
  customNode: CustomNode,
};


const edgeTypes = {
  custom: CustomEdge,
};

function App() {
  const {
    onNodeDelete,
    onEdgeDelete,
    onEdgeCreate,
    onNodeCreate,
    onSetInitialState,
  } = useGraphActions();

  // Get state from Zustand
  const {
    nodes,
    edges,
    workflows,
    selectedWorkflow,
    availableNodes,
    contextMenu,
    onNodesChange,
    onEdgesChange,
    setSelectedWorkflow,
    setContextMenu,
    updateFlowStructure,
    connected,
    initWebSocket,
  } = useStore();

  const [jsonDrawerOpen, setJsonDrawerOpen] = useState(false);

  // Add this useEffect
  React.useEffect(() => {
    initWebSocket();
  }, [initWebSocket]);

  const handleWorkflowSelect = (event: React.ChangeEvent<HTMLSelectElement>) => {
    const workflowId = event.target.value || null;
    setSelectedWorkflow(workflowId);
    updateFlowStructure();
  };

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
    <div style={{ width: '100vw', height: '100vh' }}>
      <div style={{ position: 'absolute', top: 20, left: 20, zIndex: 4 }}>
        <select onChange={handleWorkflowSelect} value={selectedWorkflow || ''}>
          <option value="">Select a workflow...</option>
          {Object.entries(workflows).map(([workflowId]) => (
            <option key={workflowId} value={workflowId}>
              {workflowId}
            </option>
          ))}
        </select>
        <span style={{ marginLeft: '10px' }}>
          {connected ? '🟢 Connected' : '🔴 Disconnected'}
        </span>
      </div>
      
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
            {availableNodes.map((node) => (
              <div
                key={node.name}
                onClick={() => {
                  onNodeCreate(node.name, `${Date.now()}`);
                  setContextMenu(null);
                }}
                style={{
                  padding: '8px 16px',
                  cursor: 'pointer',
                }}
                className="hover:bg-gray-100"
              >
                {node.name} ({node.type})
              </div>
            ))}
          </div>
        )}
      </ReactFlow>
      
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
          initialConfig={workflows[selectedWorkflow].initial_state} 
          onSave={onSetInitialState}
          open={jsonDrawerOpen}
          onOpenChange={setJsonDrawerOpen}
          title="Workflow Initial State"
          variant="workflow"
        />
      )}
    </div>
  );
}

export default App;