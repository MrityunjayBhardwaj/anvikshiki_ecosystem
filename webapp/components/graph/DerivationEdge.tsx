"use client";

import { memo } from "react";
import {
  BaseEdge,
  EdgeLabelRenderer,
  getBezierPath,
  type EdgeProps,
} from "@xyflow/react";

const EDGE_STYLES: Record<string, { color: string; dash?: string; label: string }> = {
  derivation: {
    color: "var(--prov-derivation)",
    label: "",
  },
  rule: {
    color: "var(--prov-vyapti)",
    dash: "6 3",
    label: "R",
  },
  source: {
    color: "var(--prov-source)",
    dash: "3 3",
    label: "S",
  },
};

interface DerivationEdgeData {
  edgeKind: "derivation" | "rule" | "source";
}

export const DerivationEdge = memo(function DerivationEdge({
  id,
  sourceX,
  sourceY,
  targetX,
  targetY,
  sourcePosition,
  targetPosition,
  data,
  selected,
}: EdgeProps & { data: DerivationEdgeData }) {
  const kind = data?.edgeKind ?? "derivation";
  const style = EDGE_STYLES[kind] ?? EDGE_STYLES.derivation;

  const [edgePath, labelX, labelY] = getBezierPath({
    sourceX,
    sourceY,
    targetX,
    targetY,
    sourcePosition,
    targetPosition,
    curvature: 0.25,
  });

  return (
    <>
      <BaseEdge
        id={id}
        path={edgePath}
        style={{
          stroke: style.color,
          strokeWidth: selected ? 2 : 1.2,
          strokeDasharray: style.dash,
          opacity: selected ? 1 : 0.6,
          transition: "opacity 150ms, stroke-width 150ms",
        }}
        markerEnd={`url(#prov-arrow-${kind})`}
      />
      {style.label && (
        <EdgeLabelRenderer>
          <div
            style={{
              position: "absolute",
              transform: `translate(-50%, -50%) translate(${labelX}px,${labelY}px)`,
              pointerEvents: "none",
            }}
          >
            <span
              className="text-[7px] font-mono px-0.5 rounded"
              style={{ color: style.color, opacity: 0.7 }}
            >
              {style.label}
            </span>
          </div>
        </EdgeLabelRenderer>
      )}
    </>
  );
});
