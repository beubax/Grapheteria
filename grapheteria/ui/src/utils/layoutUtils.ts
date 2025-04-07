import dagre from 'dagre';
import { Node, Edge, Position, MarkerType, InternalNode } from '@xyflow/react';

export function getLayoutedElements(nodes: Node[], edges: Edge[], direction = 'LR') {
  const dagreGraph = new dagre.graphlib.Graph({
    multigraph: true,
    compound: false
  });

  // Set graph options with balanced spacing
  dagreGraph.setDefaultEdgeLabel(() => ({}));
  dagreGraph.setGraph({
    rankdir: direction,
    ranksep: 120,     // Balanced vertical space
    nodesep: 80,      // Balanced horizontal space
    edgesep: 40,      // Space between parallel edges
    acyclicer: 'greedy',
    ranker: 'tight-tree', // Changed to tight-tree for more compact layout
    marginx: 20,      // Minimum horizontal margin
    marginy: 20,      // Minimum vertical margin
  });

  // Add nodes to dagre with reasonable size
  nodes.forEach((node) => {
    dagreGraph.setNode(node.id, { 
      width: 180,    // Balanced node width
      height: 60     // Balanced node height
    });
  });

  // Add edges with careful spacing configuration
  edges.forEach((edge, index) => {
    dagreGraph.setEdge(
      edge.source,
      edge.target,
      {
        weight: 2,    // Increased weight to prioritize edge straightness
        minlen: 1,    // Reduced minimum length for closer nodes
        labelpos: 'c',
        width: 20,    // Slimmer edge width
        height: 20,
        // Slightly offset parallel edges
        labeloffset: index * 5
      },
      edge.id
    );
  });

  // Calculate layout
  dagre.layout(dagreGraph);

  // Adjust node positioning
  const layoutedNodes = nodes.map((node) => {
    const nodeWithPosition = dagreGraph.node(node.id);
    return {
      ...node,
      position: {
        x: nodeWithPosition.x - 90,  // center the node (width / 2)
        y: nodeWithPosition.y - 30,  // center the node (height / 2)
      },
    };
  });

  return { nodes: layoutedNodes, edges };
}

// this helper function returns the intersection point
// of the line between the center of the intersectionNode and the target node
function getNodeIntersection(intersectionNode: InternalNode, targetNode: InternalNode) {
  // https://math.stackexchange.com/questions/1724792/an-algorithm-for-finding-the-intersection-point-between-a-center-of-vision-and-a
  const { width: intersectionNodeWidth = 0, height: intersectionNodeHeight = 0 } =
    intersectionNode.measured || {};
  const intersectionNodePosition = intersectionNode.position;
  const targetPosition = targetNode.position;

  const w = intersectionNodeWidth / 2;
  const h = intersectionNodeHeight / 2;
 
  const x2 = intersectionNodePosition.x + w;
  const y2 = intersectionNodePosition.y + h;
  const x1 = targetPosition.x + (targetNode.measured?.width ?? 0) / 2;
  const y1 = targetPosition.y + (targetNode.measured?.height ?? 0) / 2;
 
  const xx1 = (x1 - x2) / (2 * w) - (y1 - y2) / (2 * h);
  const yy1 = (x1 - x2) / (2 * w) + (y1 - y2) / (2 * h);
  const a = 1 / (Math.abs(xx1) + Math.abs(yy1) || 1);
  const xx3 = a * xx1;
  const yy3 = a * yy1;
  const x = w * (xx3 + yy3) + x2;
  const y = h * (-xx3 + yy3) + y2;
 
  return { x, y };
}
 
// returns the position (top,right,bottom or right) passed node compared to the intersection point
function getEdgePosition(node: InternalNode, intersectionPoint: { x: number; y: number }) {
  const n = { ...node.internals.positionAbsolute, ...node };
  const nx = Math.round(n.x);
  const ny = Math.round(n.y);
  const px = Math.round(intersectionPoint.x);
  const py = Math.round(intersectionPoint.y);
 
  if (px <= nx + 1) {
    return Position.Left;
  }
  if (px >= nx + (n.measured?.width ?? 0) - 1) {
    return Position.Right;
  }
  if (py <= ny + 1) {
    return Position.Top;
  }
  if (py >= n.y + (n.measured?.height ?? 0) - 1) {
    return Position.Bottom;
  }
 
  return Position.Top;
}
 
// returns the parameters (sx, sy, tx, ty, sourcePos, targetPos) you need to create an edge
export function getEdgeParams(source: InternalNode, target: InternalNode) {
  const sourceIntersectionPoint = getNodeIntersection(source, target);
  const targetIntersectionPoint = getNodeIntersection(target, source);
 
  const sourcePos = getEdgePosition(source, sourceIntersectionPoint);
  const targetPos = getEdgePosition(target, targetIntersectionPoint);
 
  return {
    sx: sourceIntersectionPoint.x,
    sy: sourceIntersectionPoint.y,
    tx: targetIntersectionPoint.x,
    ty: targetIntersectionPoint.y,
    sourcePos,
    targetPos,
  };
}
 
export function createNodesAndEdges() {
  const nodes = [];
  const edges = [];
  const center = { x: window.innerWidth / 2, y: window.innerHeight / 2 };
 
  nodes.push({ id: 'target', data: { label: 'Target' }, position: center });
 
  for (let i = 0; i < 8; i++) {
    const degrees = i * (360 / 8);
    const radians = degrees * (Math.PI / 180);
    const x = 250 * Math.cos(radians) + center.x;
    const y = 250 * Math.sin(radians) + center.y;
 
    nodes.push({ id: `${i}`, data: { label: 'Source' }, position: { x, y } });
 
    edges.push({
      id: `edge-${i}`,
      target: 'target',
      source: `${i}`,
      type: 'floating',
      markerEnd: {
        type: MarkerType.Arrow,
      },
    });
  }
 
  return { nodes, edges };
}

