import React from 'react';
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
    updateFlow,
    connected,
    initWebSocket,
  } = useStore();

  // Add this useEffect
  React.useEffect(() => {
    initWebSocket();
  }, [initWebSocket]);

  const handleWorkflowSelect = (event: React.ChangeEvent<HTMLSelectElement>) => {
    const workflow = workflows.find(w => w.workflow_id === event.target.value) || null;
    setSelectedWorkflow(workflow?.workflow_id || null);
    updateFlow();

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
          {workflows.map(workflow => (
            <option key={workflow.workflow_id} value={workflow.workflow_id}>
              {workflow.workflow_name || workflow.workflow_id}
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
        onNodeDoubleClick={(_, node) => onNodeDelete(node.id)}
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
    </div>
  );
}

export default App;