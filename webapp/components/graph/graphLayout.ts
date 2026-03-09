import dagre from "@dagrejs/dagre";
import type { Node, Edge } from "@xyflow/react";

export function applyDagreLayout(nodes: Node[], edges: Edge[]): Node[] {
  const g = new dagre.graphlib.Graph();
  g.setGraph({ rankdir: "BT", ranksep: 80, nodesep: 40 });
  g.setDefaultEdgeLabel(() => ({}));

  nodes.forEach((n) =>
    g.setNode(n.id, {
      width: n.measured?.width ?? 200,   // v12: use measured dimensions
      height: n.measured?.height ?? 80,
    })
  );
  edges.forEach((e) => g.setEdge(e.source, e.target));
  dagre.layout(g);

  return nodes.map((n) => {
    const pos = g.node(n.id);
    return {
      ...n,
      position: {
        x: pos.x - (n.measured?.width ?? 200) / 2,
        y: pos.y - (n.measured?.height ?? 80) / 2,
      },
    };
  });
}
