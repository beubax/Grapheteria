import { useInternalNode, useStore, getStraightPath } from '@xyflow/react';
import { CSSProperties, useState, useRef, useEffect } from 'react';
import { getEdgeParams } from '../utils/layoutUtils.ts';
import { useGraphActions } from '../utils/graphActions';
interface CustomEdgeProps {
  id: string;
  source: string;
  target: string;
  style?: CSSProperties;
  data?: {
    condition?: string;
  };
}

const CustomEdge = ({ id, source, target, style, data }: CustomEdgeProps) => {
  const [isEditing, setIsEditing] = useState(false);
  const [condition, setCondition] = useState(data?.condition || '');
  const inputRef = useRef<HTMLInputElement>(null);
  const sourceNode = useInternalNode(source);
  const targetNode = useInternalNode(target);
  const { onSetEdgeCondition } = useGraphActions();
  // Get all edges to check for bidirectional connections
  const edges = useStore((state) => state.edges);
  
  // Add useEffect to handle clicks outside the input
  useEffect(() => {
    if (!isEditing) return;
    
    const handleClickOutside = () => {
      // Save changes when clicking anywhere on the canvas
      setIsEditing(false);
    };
    
    // Add global event listener when editing is active
    document.addEventListener('click', handleClickOutside);
    
    // Clean up
    return () => {
      document.removeEventListener('click', handleClickOutside);
    };
  }, [isEditing]);
  
  if (!sourceNode || !targetNode) {
    return null;
  }

  const { sx, sy, tx, ty } = getEdgeParams(sourceNode, targetNode);
  
  // Check if bidirectional connection exists
  const hasBidirectional = edges.some(
    (edge) => edge.source === target && edge.target === source
  );
  
  // For bidirectional edges, we need to determine which direction this specific edge is going
  let edgePath = '';
  if (hasBidirectional) {
    // Calculate center point for the quadratic curve
    const centerX = (sx + tx) / 2;
    const centerY = (sy + ty) / 2;
    
    // Apply smaller offset for bidirectional edges to reduce visual clutter
    const isSourceToTarget = source < target; // Simple heuristic to decide direction
    const offset = isSourceToTarget ? 20 : -20; // Reduced from 25 to 20
    
    // Create a custom quadratic curve path with offset
    edgePath = `M ${sx} ${sy} Q ${centerX} ${centerY + offset} ${tx} ${ty}`;
  } else {
    // Use straight path for single-direction edges
    [edgePath] = getStraightPath({
      sourceX: sx,
      sourceY: sy,
      targetX: tx,
      targetY: ty,
    });
  }

  // Calculate the position for the button (center of the edge)
  const centerX = (sx + tx) / 2;
  const centerY = (sy + ty) / 2;

  // Position adjustment for bidirectional edges
  const buttonOffset = hasBidirectional 
    ? (source < target ? 20 : -20) 
    : 0;

  // Effect to focus the input when editing starts
  useEffect(() => {
    if (isEditing && inputRef.current) {
      inputRef.current.focus();
    }
  }, [isEditing]);

  const handleButtonClick = (e: React.MouseEvent) => {
    e.stopPropagation();
    setIsEditing(true);
  };

  const handleSave = () => {
    onSetEdgeCondition(source, target, condition);
    setIsEditing(false);
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter') {
      handleSave();
    } else if (e.key === 'Escape') {
      setIsEditing(false);
    }
  };

  return (
    <>
      <defs>
        <marker
          id="custom-arrow"
          viewBox="0 0 10 10"
          refX="10"
          refY="5"
          markerWidth="5"
          markerHeight="5"
          orient="auto-start-reverse"
        >
          <path d="M 0 0 L 10 5 L 0 10 z" fill="#b1b1b7" />
        </marker>
      </defs>
      
      {/* Invisible wider path for easier edge selection/deletion */}
      <path
        d={edgePath}
        stroke="transparent"
        strokeWidth={15}
        fill="none"
        style={{ cursor: 'pointer' }}
      />
      
      <path
        id={id}
        className="react-flow__edge-path"
        d={edgePath}
        markerEnd="url(#custom-arrow)"
        style={{ 
          stroke: '#b1b1b7', 
          strokeWidth: 2.5, 
          strokeDasharray: hasBidirectional ? '5, 5' : 'none',
          ...style 
        }}
      />

      {/* Condition button - improved visibility */}
      <foreignObject
        width={28}
        height={28}
        x={centerX - 14}
        y={centerY + buttonOffset - 14}
        className="edge-button-container"
        style={{ 
          pointerEvents: isEditing ? 'none' : 'all'
        }}
      >
        <div 
          onClick={handleButtonClick}
          style={{
            width: '100%',
            height: '100%',
            background: condition ? '#e6f7ff' : '#f5f5f5',
            border: `1px solid ${condition ? '#1890ff' : '#ccc'}`,
            borderRadius: '50%',
            display: 'flex',
            justifyContent: 'center',
            alignItems: 'center',
            cursor: 'pointer',
            fontSize: '14px',
            transform: isEditing ? 'scale(0)' : 'scale(1)',
            transition: 'transform 0.2s, background-color 0.2s',
            zIndex: 10,
            boxShadow: '0 2px 4px rgba(0,0,0,0.1)'
          }}
          title={condition ? `Condition: ${condition}` : "Add condition"}
        >
          {condition ? "✓" : "+"}
        </div>
      </foreignObject>

      {/* Condition input (appears when editing) */}
      {isEditing && (
        <foreignObject
          width={180}
          height={40}
          x={centerX - 90}
          y={centerY + buttonOffset - 20}
          className="edge-input-container"
          style={{ 
            pointerEvents: 'all'
          }}
          onMouseDown={(e) => e.stopPropagation()}
          onClick={(e) => e.stopPropagation()}
          onDoubleClick={(e) => e.stopPropagation()}
        >
          <div 
            style={{
              background: 'white',
              borderRadius: '4px',
              boxShadow: '0 2px 5px rgba(0,0,0,0.15)',
              padding: '3px',
              width: '100%',
              height: '100%',
              display: 'flex',
              alignItems: 'center'
            }}
            onClick={(e) => e.stopPropagation()}
            onDoubleClick={(e) => e.stopPropagation()}
            onMouseDown={(e) => e.stopPropagation()}
          >
            <input
              ref={inputRef}
              value={condition}
              onChange={(e) => setCondition(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder="Enter condition..."
              style={{
                border: 'none',
                outline: 'none',
                width: '100%',
                padding: '5px',
                fontSize: '12px'
              }}
              onClick={(e) => e.stopPropagation()}
              onDoubleClick={(e) => e.stopPropagation()}
              onMouseDown={(e) => e.stopPropagation()}
            />
            <div 
              onClick={(e) => {
                e.stopPropagation();
                handleSave();
              }}
              onDoubleClick={(e) => e.stopPropagation()}
              onMouseDown={(e) => e.stopPropagation()}
              style={{
                cursor: 'pointer',
                padding: '3px 5px',
                background: '#4CAF50',
                color: 'white',
                borderRadius: '3px',
                fontSize: '12px'
              }}
            >
              Save
            </div>
          </div>
        </foreignObject>
      )}
    </>
  );
}

export default CustomEdge;