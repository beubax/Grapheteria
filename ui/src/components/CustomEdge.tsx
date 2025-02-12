import { getStraightPath, useInternalNode } from '@xyflow/react';
import { CSSProperties } from 'react';
import { getEdgeParams } from '../utils/layoutUtils.ts';

interface CustomEdgeProps {
  id: string;
  source: string;
  target: string;
  style?: CSSProperties;
}

const CustomEdge = ({ id, source, target, style }: CustomEdgeProps) => {
  const sourceNode = useInternalNode(source);
  const targetNode = useInternalNode(target);

  if (!sourceNode || !targetNode) {
    return null;
  }

  const { sx, sy, tx, ty } = getEdgeParams(sourceNode, targetNode);

  const [edgePath] = getStraightPath({
    sourceX: sx,
    sourceY: sy,
    targetX: tx,
    targetY: ty,
  });

  return (
    <>
      <defs>
        <marker
          id="custom-arrow"
          viewBox="0 0 10 10"
          refX="10"
          refY="5"
          markerWidth="8"
          markerHeight="8"
          orient="auto-start-reverse"
        >
          <path d="M 0 0 L 10 5 L 0 10 z" fill="#b1b1b7" />
        </marker>
      </defs>
      <path
        id={id}
        className="react-flow__edge-path"
        d={edgePath}
        markerEnd="url(#custom-arrow)"
        style={{ stroke: '#b1b1b7', ...style }}
      />
    </>
  );
}

export default CustomEdge;