import { Handle, Position, useConnection } from '@xyflow/react';
import useStore from '../stores/useStore';
import { useState, useCallback } from 'react';
import { useGraphActions } from '../utils/graphActions';
import { JSONDrawer } from './JSONDrawer';

interface CustomNodeProps {
  id: string;
  data: {
    label: string;
    nodeType: string;
    status?: "queued" | "completed" | "failed" | "pending" | "waiting_for_input";
    isStartNode?: boolean;
    config?: any;
  };
}

export default function CustomNode({ id, data }: CustomNodeProps) {
  const connection = useConnection();
  const debugMode = useStore(state => state.debugMode);
  const [contextMenu, setContextMenu] = useState<{ x: number, y: number } | null>(null);
  const { onMarkAsStartNode, onSaveNodeConfig } = useGraphActions();
  const [configOpen, setConfigOpen] = useState(false);
 
  const isTarget = connection.inProgress && connection.fromNode.id !== id;

  // Status color mapping
  const statusColors = {
    queued: 'bg-blue-100 text-blue-700 border-blue-300',
    completed: 'bg-green-100 text-green-700 border-green-300',
    failed: 'bg-red-100 text-red-700 border-red-300',
    pending: 'bg-gray-100 text-gray-700 border-gray-300',
    waiting_for_input: 'bg-amber-100 text-amber-700 border-amber-300'
  };

  const nodeStatusClass = data.status && debugMode ? statusColors[data.status] : 'bg-white border-[#ddd]';
  
  const handleContextMenu = useCallback((event: React.MouseEvent) => {
    event.preventDefault();
    event.stopPropagation();
    
    // Get correct position for the context menu
    const boundingRect = (event.currentTarget as HTMLElement).getBoundingClientRect();
    const x = event.clientX - boundingRect.left;
    const y = event.clientY - boundingRect.top;
    
    setContextMenu({ x, y });
    
    // Add a click listener to the document to close the context menu when clicking elsewhere
    const closeContextMenu = () => {
      setContextMenu(null);
      document.removeEventListener('click', closeContextMenu);
      document.removeEventListener('contextmenu', closeContextMenu);
    };
    
    // Add the listeners with a slight delay to avoid immediate triggering
    setTimeout(() => {
      document.addEventListener('click', closeContextMenu);
      document.addEventListener('contextmenu', closeContextMenu);
    }, 0);
  }, []);
  
  const handleMarkAsStartNode = useCallback(() => {
    onMarkAsStartNode(id);
    setContextMenu(null);
  }, [id, onMarkAsStartNode]);
 
  return (
    <>
      <div 
        className={`p-2.5 rounded border relative ${nodeStatusClass} ${data.isStartNode ? 'ring-2 ring-blue-500' : ''}`}
        onContextMenu={handleContextMenu}
      >
        {debugMode && data.status && (
          <div className="absolute -top-2 -right-2 text-xs font-semibold px-2 py-0.5 rounded-full bg-white border shadow-sm">
            {data.status}
          </div>
        )}
        {data.isStartNode && (
          <div className="absolute -top-2 -left-2 text-xs font-semibold px-2 py-0.5 rounded-full bg-blue-500 text-white">
            Start
          </div>
        )}
        <div className="relative flex items-center justify-between">
          <div className="flex-1">
            {!connection.inProgress && (
              <Handle
                id={`${id}-source`}
                className="!w-full !h-full !bg-blue-500 !absolute !top-0 !left-0 !rounded-none !transform-none !border-0 !opacity-0"
                position={Position.Right}
                type="source"
              />
            )}
            {(!connection.inProgress || isTarget) && (
              <Handle 
                id={`${id}-target`}
                className="!w-full !h-full !bg-blue-500 !absolute !top-0 !left-0 !rounded-none !transform-none !border-0 !opacity-0"
                position={Position.Left}
                type="target"
                isConnectableStart={false}
              />
            )}
            {data.label}
          </div>
        </div>
      </div>
      
      {contextMenu && (
        <div
          className="absolute z-50 bg-white shadow-lg rounded-md overflow-hidden w-40 text-sm"
          style={{ left: contextMenu.x, top: contextMenu.y }}
          onClick={(e) => e.stopPropagation()}
        >
          <div 
            className="px-2 py-1 hover:bg-gray-100 cursor-pointer"
            onClick={handleMarkAsStartNode}
          >
            Mark as start node
          </div>
          <div 
            className="px-2 py-1 hover:bg-gray-100 cursor-pointer"
            onClick={() => {
              setConfigOpen(true);
              setContextMenu(null);
            }}
          >
            Configure node
          </div>
          <div 
            className="px-2 py-1 hover:bg-gray-100 cursor-pointer"
            onClick={() => setContextMenu(null)}
          >
            Cancel
          </div>
        </div>
      )}
      
      <JSONDrawer
        initialConfig={data.config || {}}
        onSave={(config) => {
         onSaveNodeConfig(id, config)
        }}
        open={configOpen}
        onOpenChange={setConfigOpen}
        title={`Configure ${data.label}`}
        variant="node"
      />
    </>
  );
}