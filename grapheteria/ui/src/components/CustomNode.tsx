import React, { useState, useRef, useEffect, useCallback } from 'react';
import { Handle, Position, useConnection } from '@xyflow/react';
import useStore from '../stores/useStore';
import { useGraphActions } from '../utils/graphActions';
import { JSONDrawer } from './JSONDrawer';
import { CodeEditor } from './CodeEditor';
import ReactDOM from 'react-dom';

interface CustomNodeProps {
  id: string;
  data: {
    class: string;
    status?: "queued" | "completed" | "failed" | "pending" | "waiting_for_input";
    isStartNode?: boolean;
    config?: any;
    requestDetails?: any;
    code?: string;
    module?: string;
  };
}

export default function CustomNode({ id, data }: CustomNodeProps) {
  const connection = useConnection();
  const debugMode = useStore(state => state.debugMode);
  const [contextMenu, setContextMenu] = useState<{ x: number, y: number } | null>(null);
  const { onMarkAsStartNode, onSaveNodeConfig, onUpdateNodeCode } = useGraphActions();
  const [configOpen, setConfigOpen] = useState(false);
  const [codeEditorOpen, setCodeEditorOpen] = useState(false);
  const [showDetails, setShowDetails] = useState(false);
  const detailsRef = useRef<HTMLDivElement>(null);
  const nodeRef = useRef<HTMLDivElement>(null);
 
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
  const isAwaitingInput = debugMode && data.status === 'waiting_for_input' && data.requestDetails;
  
  // Calculate position for the details dropdown
  const [detailsPosition, setDetailsPosition] = useState({ top: 0, left: 0 });
  
  useEffect(() => {
    if (showDetails && nodeRef.current) {
      const rect = nodeRef.current.getBoundingClientRect();
      setDetailsPosition({
        top: rect.bottom + window.scrollY,
        left: rect.left + window.scrollX
      });
    }
  }, [showDetails]);
  
  // Close dropdown when clicking outside
  useEffect(() => {
    if (!showDetails) return;
    
    const handleClickOutside = (event: MouseEvent) => {
      if (detailsRef.current && !detailsRef.current.contains(event.target as Node)) {
        setShowDetails(false);
      }
    };
    
    document.addEventListener('mousedown', handleClickOutside);
    return () => {
      document.removeEventListener('mousedown', handleClickOutside);
    };
  }, [showDetails]);
  
  const handleContextMenu = useCallback((event: React.MouseEvent) => {
    event.preventDefault();
    event.stopPropagation();
    // Position at the bottom right corner with a small offset
    const x = 80; // Position relative to the node
    const y = 50; // Just below the node with a small gap
    
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

  const toggleDetails = (e: React.MouseEvent) => {
    e.stopPropagation();
    e.preventDefault();
    setShowDetails(prev => !prev);
  };
 
  // Render details dropdown using portal
  const renderDetailsPortal = () => {
    if (!showDetails || !isAwaitingInput) return null;
    
    return ReactDOM.createPortal(
      <div 
        ref={detailsRef}
        className="fixed bg-white border-2 border-amber-200 rounded-md shadow-lg z-50 w-64 overflow-hidden"
        style={{ 
          top: detailsPosition.top + 'px', 
          left: detailsPosition.left + 'px' 
        }}
      >
        <div className="max-h-60 overflow-y-auto p-2">
          <div className="font-medium text-amber-700 text-xs border-b border-amber-100 pb-1 mb-2">
            Input Request Details
          </div>
          {data.requestDetails && (
            <pre 
              className="text-xs whitespace-pre-wrap bg-gray-50 p-2 rounded font-mono overflow-x-auto user-select-all"
            >
              {JSON.stringify(data.requestDetails, null, 2)}
            </pre>
          )}
        </div>
      </div>,
      document.body
    );
  };
 
  return (
    <>
      <div 
        ref={nodeRef}
        className={`p-3 rounded-lg border-2 relative transition-all duration-200 shadow-sm hover:shadow-md
                    ${nodeStatusClass} 
                    ${data.isStartNode ? 'ring-2 ring-blue-500' : ''}`}
        onContextMenu={handleContextMenu}
      >
        {/* Full-node source handle (center position) */}
        {!connection.inProgress && (
          <Handle
            id={`${id}-source`}
            className="!w-full !h-full !bg-transparent !absolute !top-0 !left-0 !rounded-none !transform-none !border-0 !opacity-0"
            position={Position.Bottom}
            type="source"
            style={{
              zIndex: 1,
              right: '50%',
              left: '50%',
              bottom: '50%',
              top: '50%'
            }}
          />
        )}
        
        {/* Full-node target handle (center position) */}
        {(!connection.inProgress || isTarget) && (
          <Handle 
            id={`${id}-target`}
            className="!w-full !h-full !bg-transparent !absolute !top-0 !left-0 !rounded-none !transform-none !border-0 !opacity-0"
            position={Position.Top}
            type="target"
            isConnectableStart={false}
            style={{
              zIndex: 1,
              right: '50%',
              left: '50%',
              bottom: '50%',
              top: '50%'
            }}
          />
        )}

        {/* Drag handle at the bottom */}
        <div 
          className="absolute bottom-0 left-1/2 transform -translate-x-1/2 translate-y-1/2 w-8 h-2 bg-gray-300 rounded-full cursor-move hover:bg-gray-400 transition-colors duration-150 flex items-center justify-center"
          style={{ zIndex: 10 }}
        >
          <div className="w-4 h-0.5 bg-gray-500 rounded-full"></div>
        </div>

        {debugMode && data.status && (
          <div className="absolute -top-5 -right-10 text-xs font-semibold px-2 py-0.5 rounded-full bg-white border shadow-sm">
            {data.status}
          </div>
        )}
        {data.isStartNode && (
          <div className="absolute -top-2 -left-2 text-xs font-semibold px-2 py-0.5 rounded-full bg-blue-500 text-white shadow-sm">
            Start
          </div>
        )}
        <div className="relative flex items-center justify-between">
          <div className="flex-1">
            <div className="font-medium">{data.class}</div>
            
            {isAwaitingInput && (
              <button
                onClick={toggleDetails}
                className="mt-2 text-xs px-2 py-1 bg-amber-50 border border-amber-200 rounded text-amber-700 hover:bg-amber-100 transition-colors duration-200 relative z-10 pointer-events-auto"
              >
                {showDetails ? 'Hide' : 'View'} Input Request
              </button>
            )}
          </div>
        </div>
      </div>
      
      {/* Render the details dropdown using portal */}
      {renderDetailsPortal()}
      
      {contextMenu && (
        <div
          className="absolute z-50 bg-white shadow-lg rounded-md overflow-hidden border border-gray-200 w-48 text-sm"
          style={{ left: contextMenu.x, top: contextMenu.y }}
          onClick={(e) => e.stopPropagation()}
          onMouseDown={(e) => e.stopPropagation()}
        >
          <div 
            className="px-3 py-2 hover:bg-gray-50 cursor-pointer flex items-center text-gray-700"
            onClick={handleMarkAsStartNode}
            onMouseDown={(e) => e.stopPropagation()}
          >
            <div className="w-5 h-5 mr-2 flex items-center justify-center">
              <span className="text-blue-500">🚀</span>
            </div>
            Mark as start node
          </div>
          <div 
            className="px-3 py-2 hover:bg-gray-50 cursor-pointer flex items-center text-gray-700"
            onClick={() => {
              setConfigOpen(true);
              setContextMenu(null);
            }}
            onMouseDown={(e) => e.stopPropagation()}
          >
            <div className="w-5 h-5 mr-2 flex items-center justify-center">
              <span className="text-gray-600">⚙️</span>
            </div>
            Configure node
          </div>
          {data.code !== undefined && (
            <div 
              className="px-3 py-2 hover:bg-gray-50 cursor-pointer flex items-center text-gray-700"
              onClick={() => {
                setCodeEditorOpen(true);
                setContextMenu(null);
              }}
              onMouseDown={(e) => e.stopPropagation()}
            >
              <div className="w-5 h-5 mr-2 flex items-center justify-center">
                <span className="text-gray-600">📝</span>
              </div>
              View/Edit code
            </div>
          )}
          <div 
            className="px-3 py-2 hover:bg-gray-50 cursor-pointer flex items-center text-gray-700"
            onClick={() => setContextMenu(null)}
            onMouseDown={(e) => e.stopPropagation()}
          >
            <div className="w-5 h-5 mr-2 flex items-center justify-center">
              <span className="text-gray-600">✖️</span>
            </div>
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
        title={`Modify Node Config`}
        variant="node"
      />
      
      {data.code !== undefined && (
        <CodeEditor
          key={data.code}
          initialCode={data.code
            ?.split('\n')
            .slice(1) // Remove the first line (class definition)
            .map(line => line.startsWith('    ') ? line.substring(4) : line) // Remove one level of indentation
            .join('\n')}
          onSave={(updatedCode) => {
            if (data.module && updatedCode.trim() !== '') {
              // Restore class definition and proper indentation
              const formattedCode = `class ${data.class}(Node):\n${updatedCode.split('\n').map(line => '    ' + line).join('\n')}`;
              onUpdateNodeCode(data.module, data.class, formattedCode);
            }
          }}
          open={codeEditorOpen}
          onOpenChange={setCodeEditorOpen}
          language="python"
          module={data.module}
          className={data.class}
          classNameEditable={false}
        />
      )}
    </>
  );
}