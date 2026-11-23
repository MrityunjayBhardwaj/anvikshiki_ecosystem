"use client";

import { memo } from "react";
import { Handle, Position, type NodeProps } from "@xyflow/react";
import { BookOpen } from "lucide-react";
import type { SourceNodeData } from "./buildProvenanceGraph";

export const SourceNode = memo(function SourceNode({
  data,
  selected,
}: NodeProps & { data: SourceNodeData }) {
  const { sourceId, referencedBy } = data;
  // Scale node slightly by reference count (min 1, max 1.15)
  const scale = Math.min(1.15, 1 + referencedBy * 0.03);

  return (
    <div
      className={`
        group relative rounded-lg border bg-card text-card-foreground shadow-sm
        px-2.5 py-1.5 min-w-[120px] max-w-[180px]
        transition-all duration-150
        ${selected ? "ring-2 ring-[var(--prov-source)] shadow-lg scale-105" : ""}
      `}
      style={{
        borderColor: "var(--prov-source)",
        borderWidth: selected ? 2 : 1,
        transform: selected ? undefined : `scale(${scale})`,
      }}
    >
      <Handle type="source" position={Position.Top} className="!w-1.5 !h-1.5 !bg-[var(--prov-source)]" />

      <div className="flex items-center gap-1.5">
        <div
          className="w-5 h-5 rounded flex items-center justify-center shrink-0"
          style={{ backgroundColor: "var(--prov-source)", opacity: 0.15 }}
        >
          <BookOpen className="w-3 h-3" style={{ color: "var(--prov-source)" }} />
        </div>
        <div className="min-w-0 flex-1">
          <p
            className="text-[10px] font-mono truncate"
            style={{ color: "var(--prov-source)" }}
            title={sourceId}
          >
            {sourceId}
          </p>
          <p className="text-[8px] text-muted-foreground">
            {referencedBy} ref{referencedBy !== 1 ? "s" : ""}
          </p>
        </div>
      </div>
    </div>
  );
});
