import { Handle, Position, useConnection } from '@xyflow/react';

interface CustomNodeProps {
  id: string;
  data: {
    label: string;
    nodeType: string;
  };
}

export default function CustomNode({ id, data }: CustomNodeProps) {
  const connection = useConnection();
 
  const isTarget = connection.inProgress && connection.fromNode.id !== id;
 
  return (
    <div className="p-2.5 rounded bg-white border border-[#ddd]">
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