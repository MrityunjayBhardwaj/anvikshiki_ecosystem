"use client";

import { memo } from "react";
import { Handle, Position, type NodeProps } from "@xyflow/react";
import { Badge } from "@/components/ui/badge";
import type { ArgumentNode as ArgNodeType } from "@/lib/types";

const LABEL_STYLE: Record<string, string> = {
  in: "border-[var(--label-in)] text-[var(--label-in)]",
  out: "border-[var(--label-out)] text-[var(--label-out)]",
  undecided: "border-[var(--label-undecided)] text-[var(--label-undecided)]",
};

const RULE_DOT: Record<string, string> = {
  strict: "bg-blue-400",
  defeasible: "bg-amber-400",
};

interface NodeData {
  arg: ArgNodeType;
  label: string;
}

export const ArgumentNode = memo(function ArgumentNode({
  data,
  selected,
}: NodeProps & { data: NodeData }) {
  const { arg } = data;

  return (
    <div
      className={`
        w-48 rounded-lg border bg-card text-card-foreground shadow-sm px-3 py-2 space-y-1.5
        transition-all duration-150
        ${selected ? "ring-2 ring-primary shadow-lg scale-105" : ""}
      `}
    >
      <Handle type="target" position={Position.Bottom} className="!w-2 !h-2" />

      {/* Header row */}
      <div className="flex items-center justify-between gap-1">
        <div className="flex items-center gap-1">
          <div
            className={`w-1.5 h-1.5 rounded-full shrink-0 ${RULE_DOT[arg.rule_type] ?? "bg-muted"}`}
            title={arg.rule_type}
          />
          <span className="text-[10px] font-mono text-muted-foreground truncate max-w-[80px]">
            {arg.id.slice(0, 8)}
          </span>
        </div>
        <Badge
          variant="outline"
          className={`text-[9px] font-mono uppercase px-1 py-0 h-4 ${LABEL_STYLE[arg.label]}`}
        >
          {arg.label}
        </Badge>
      </div>

      {/* Conclusion */}
      <p className="text-xs leading-snug line-clamp-2">{arg.conclusion}</p>

      {/* Provenance: the channel the claim arrived through, and how fresh
          it is. There is no belief bar any more — an argument's grade is a
          position in the lattice, shown below, not a fraction of a bar. */}
      <div className="flex justify-between text-[9px] font-mono text-muted-foreground">
        <span className="lowercase">{arg.tag.pramana_type}</span>
        <span>depth={arg.tag.derivation_depth}</span>
      </div>

      {/* Epistemic status */}
      {arg.epistemic_status && (
        <div
          className="text-[9px] font-mono text-muted-foreground capitalize"
          style={{ color: `var(--${arg.epistemic_status})` }}
        >
          {arg.epistemic_status}
        </div>
      )}

      <Handle type="source" position={Position.Top} className="!w-2 !h-2" />
    </div>
  );
});
