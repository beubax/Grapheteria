import { getStraightPath } from '@xyflow/react';

interface CustomConnectionLineProps {
  fromX: number;
  fromY: number;
  toX: number;
  toY: number;
}

function CustomConnectionLine({ fromX, fromY, toX, toY }: CustomConnectionLineProps) {
  const [edgePath] = getStraightPath({
    sourceX: fromX,
    sourceY: fromY,
    targetX: toX,
    targetY: toY,
  });
 
  return (
    <g>
      <path style={{ stroke: '#b1b1b7' }} fill="none" d={edgePath} />
    </g>
  );
}

export default CustomConnectionLine;