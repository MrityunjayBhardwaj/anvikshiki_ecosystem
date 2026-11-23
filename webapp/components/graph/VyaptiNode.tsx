"use client";

import { memo } from "react";
import { Handle, Position, type NodeProps } from "@xyflow/react";
import { Workflow } from "lucide-react";
import type { VyaptiNodeData } from "./buildProvenanceGraph";

export const VyaptiNode = memo(function VyaptiNode({
  data,
  selected,
}: NodeProps & { data: VyaptiNodeData }) {
  const { vyaptiId, usedBy } = data;

  return (
    <div
      className={`
        group relative border bg-card text-card-foreground shadow-sm
        px-2.5 py-1.5 min-w-[110px] max-w-[170px]
        transition-all duration-150
      `}
      style={{
        borderColor: "var(--prov-vyapti)",
        borderWidth: selected ? 2 : 1,
        // Diamond shape via clip-path at container, but keep readable —
        // use a subtle rotated-square border instead
        borderRadius: "4px",
        background: selected
          ? "color-mix(in oklch, var(--prov-vyapti) 8%, var(--card))"
          : undefined,
        boxShadow: selected ? "0 0 12px color-mix(in oklch, var(--prov-vyapti) 30%, transparent)" : undefined,
      }}
    >
      <Handle type="target" position={Position.Bottom} className="!w-1.5 !h-1.5 !bg-[var(--prov-vyapti)]" />
      <Handle type="source" position={Position.Top} className="!w-1.5 !h-1.5 !bg-[var(--prov-vyapti)]" />

      <div className="flex items-center gap-1.5">
        <div
          className="w-5 h-5 rounded flex items-center justify-center shrink-0"
          style={{ backgroundColor: "var(--prov-vyapti)", opacity: 0.15 }}
        >
          <Workflow className="w-3 h-3" style={{ color: "var(--prov-vyapti)" }} />
        </div>
        <div className="min-w-0 flex-1">
          <p
            className="text-[10px] font-mono font-medium truncate"
            style={{ color: "var(--prov-vyapti)" }}
            title={vyaptiId}
          >
            {vyaptiId}
          </p>
          <p className="text-[8px] text-muted-foreground">
            rule | {usedBy} use{usedBy !== 1 ? "s" : ""}
          </p>
        </div>
      </div>
    </div>
  );
});
