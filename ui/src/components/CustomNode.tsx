import { Handle, Position, useConnection } from '@xyflow/react';
import useStore from '../stores/useStore';

interface CustomNodeProps {
  id: string;
  data: {
    label: string;
    nodeType: string;
    status?: "queued" | "completed" | "failed" | "pending";
  };
}

export default function CustomNode({ id, data }: CustomNodeProps) {
  const connection = useConnection();
  const debugMode = useStore(state => state.debugMode);
 
  const isTarget = connection.inProgress && connection.fromNode.id !== id;

  // Status color mapping
  const statusColors = {
    queued: 'bg-blue-100 text-blue-700 border-blue-300',
    completed: 'bg-green-100 text-green-700 border-green-300',
    failed: 'bg-red-100 text-red-700 border-red-300',
    pending: 'bg-gray-100 text-gray-700 border-gray-300'
  };

  const nodeStatusClass = data.status && debugMode ? statusColors[data.status] : 'bg-white border-[#ddd]';
 
  return (
    <div className={`p-2.5 rounded border relative ${nodeStatusClass}`}>
      {debugMode && data.status && (
        <div className="absolute -top-2 -right-2 text-xs font-semibold px-2 py-0.5 rounded-full bg-white border shadow-sm">
          {data.status}
        </div>
      )}
      <div className="relative flex items-center">
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
  );
}