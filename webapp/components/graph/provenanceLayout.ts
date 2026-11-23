/**
 * Multi-layer layout for the provenance chain graph.
 *
 * Uses Dagre with bottom-to-top ranking.
 * Node layers are hinted by assigning rank groups:
 *   - source nodes → lowest rank (bottom)
 *   - vyapti nodes → middle-low
 *   - premise argument nodes → middle
 *   - derived argument nodes → top
 */

import dagre from "@dagrejs/dagre";
import type { Node, Edge } from "@xyflow/react";

interface LayoutOptions {
  /** Direction: BT = bottom-to-top (default), TB = top-to-bottom, LR, RL */
  rankdir?: "BT" | "TB" | "LR" | "RL";
  /** Vertical spacing between ranks */
  ranksep?: number;
  /** Horizontal spacing between nodes in same rank */
  nodesep?: number;
}

// Default dimensions per node type
const NODE_DIMENSIONS: Record<string, { width: number; height: number }> = {
  source: { width: 160, height: 44 },
  vyapti: { width: 150, height: 44 },
  provenanceArg: { width: 220, height: 110 },
  argument: { width: 200, height: 80 },
};

export function applyProvenanceLayout(
  nodes: Node[],
  edges: Edge[],
  options: LayoutOptions = {},
): Node[] {
  const { rankdir = "BT", ranksep = 100, nodesep = 50 } = options;

  const g = new dagre.graphlib.Graph();
  g.setGraph({ rankdir, ranksep, nodesep, marginx: 40, marginy: 40 });
  g.setDefaultEdgeLabel(() => ({}));

  // Add nodes with dimensions
  for (const node of nodes) {
    const dims =
      NODE_DIMENSIONS[node.type ?? "argument"] ??
      NODE_DIMENSIONS.argument;
    g.setNode(node.id, {
      width: node.measured?.width ?? dims.width,
      height: node.measured?.height ?? dims.height,
    });
  }

  // Add edges
  for (const edge of edges) {
    // Only add edge if both ends exist
    if (g.hasNode(edge.source) && g.hasNode(edge.target)) {
      g.setEdge(edge.source, edge.target);
    }
  }

  dagre.layout(g);

  return nodes.map((node) => {
    const pos = g.node(node.id);
    if (!pos) return node; // disconnected node — keep original position
    const dims =
      NODE_DIMENSIONS[node.type ?? "argument"] ??
      NODE_DIMENSIONS.argument;
    return {
      ...node,
      position: {
        x: pos.x - (node.measured?.width ?? dims.width) / 2,
        y: pos.y - (node.measured?.height ?? dims.height) / 2,
      },
    };
  });
}
