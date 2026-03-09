"use client";

import { memo } from "react";
import { BaseEdge, EdgeLabelRenderer, getStraightPath, type EdgeProps } from "@xyflow/react";
import type { AttackEdge as AttackEdgeType } from "@/lib/types";

const EDGE_COLOR: Record<string, string> = {
  rebuttal:     "var(--attack-rebuttal)",
  undercutting: "var(--attack-undercutting)",
  undermining:  "var(--attack-undermining)",
};

interface EdgeData {
  attack: AttackEdgeType;
}

export const AttackEdge = memo(function AttackEdge({
  id,
  sourceX,
  sourceY,
  targetX,
  targetY,
  data,
}: EdgeProps & { data: EdgeData }) {
  const { attack } = data;
  const color = EDGE_COLOR[attack.attack_type] ?? "#888";
  const [edgePath, labelX, labelY] = getStraightPath({
    sourceX,
    sourceY,
    targetX,
    targetY,
  });

  return (
    <>
      <BaseEdge
        id={id}
        path={edgePath}
        style={{ stroke: color, strokeWidth: 1.5, strokeDasharray: attack.attack_type === "undermining" ? "4 2" : undefined }}
        markerEnd={`url(#arrow-${attack.attack_type})`}
      />
      <EdgeLabelRenderer>
        <div
          style={{
            position: "absolute",
            transform: `translate(-50%, -50%) translate(${labelX}px,${labelY}px)`,
            pointerEvents: "all",
          }}
        >
          <span
            className="text-[9px] font-mono px-1 py-0.5 rounded bg-background border"
            style={{ color, borderColor: color }}
            title={`${attack.attack_type}${attack.hetvabhasa ? ` (${attack.hetvabhasa})` : ""}`}
          >
            {attack.attack_type[0].toUpperCase()}
          </span>
        </div>
      </EdgeLabelRenderer>
    </>
  );
});
