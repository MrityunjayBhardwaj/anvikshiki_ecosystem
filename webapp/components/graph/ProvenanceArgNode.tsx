"use client";

import { memo } from "react";
import { Handle, Position, type NodeProps } from "@xyflow/react";
import { Badge } from "@/components/ui/badge";
import { Eye, Brain, MessageSquare, Ruler } from "lucide-react";
import type { ArgChainNodeData } from "./buildProvenanceGraph";

const PRAMANA_ICON: Record<string, React.ElementType> = {
  PRATYAKSA: Eye,
  ANUMANA: Brain,
  SABDA: MessageSquare,
  UPAMANA: Ruler,
};

const LABEL_BORDER: Record<string, string> = {
  in: "var(--label-in)",
  out: "var(--label-out)",
  undecided: "var(--label-undecided)",
};

const LABEL_STYLE: Record<string, string> = {
  in: "border-[var(--label-in)] text-[var(--label-in)]",
  out: "border-[var(--label-out)] text-[var(--label-out)]",
  undecided: "border-[var(--label-undecided)] text-[var(--label-undecided)]",
};

export const ProvenanceArgNode = memo(function ProvenanceArgNode({
  data,
  selected,
}: NodeProps & { data: ArgChainNodeData }) {
  const { arg, isPremise } = data;
  const PramIcon = PRAMANA_ICON[arg.tag.pramana_type] ?? Ruler;
  const borderColor = LABEL_BORDER[arg.label] ?? "var(--border)";

  return (
    <div
      className={`
        w-52 rounded-lg border bg-card text-card-foreground shadow-sm
        px-3 py-2 space-y-1
        transition-all duration-150
        ${selected ? "ring-2 ring-primary shadow-lg scale-105" : ""}
      `}
      style={{
        borderColor,
        borderWidth: selected ? 2 : 1.5,
        borderLeftWidth: 3,
      }}
    >
      <Handle type="target" position={Position.Bottom} className="!w-2 !h-2" />

      {/* Header row */}
      <div className="flex items-center justify-between gap-1">
        <div className="flex items-center gap-1">
          {/* Premise/derived indicator */}
          <div
            className="w-1.5 h-1.5 rounded-full shrink-0"
            style={{
              backgroundColor: isPremise
                ? "var(--prov-premise)"
                : "var(--prov-derived)",
            }}
            title={isPremise ? "Premise (base fact)" : "Derived (rule-based)"}
          />
          <PramIcon
            className="w-3 h-3 shrink-0"
            style={{ color: `var(--pramana-${arg.tag.pramana_type.toLowerCase()})` }}
          />
          <span className="text-[9px] font-mono text-muted-foreground truncate max-w-[80px]">
            {arg.id.slice(0, 10)}
          </span>
        </div>
        <Badge
          variant="outline"
          className={`text-[8px] font-mono uppercase px-1 py-0 h-3.5 ${LABEL_STYLE[arg.label]}`}
        >
          {arg.label}
        </Badge>
      </div>

      {/* Conclusion */}
      <p className="text-[11px] leading-snug line-clamp-2 font-medium">
        {arg.conclusion}
      </p>

      {/* The belief/disbelief/uncertainty bar that was here is gone with the
          opinion arithmetic behind it — an argument's grade is now its
          epistemic status, a position in a five-value lattice, which the
          bottom row already renders. Left as trust and freshness, the two
          provenance magnitudes that survive.

          MINIMAL STAND-IN: written only to keep the typecheck passing after
          the tag lost its triple. This is your in-progress component and the
          visual call is yours — swap it for whatever reads best. */}
      <div className="flex justify-between text-[8px] font-mono text-muted-foreground">
        <span>trust={arg.tag.trust_score.toFixed(2)}</span>
        <span>decay={arg.tag.decay_factor.toFixed(2)}</span>
      </div>

      {/* Bottom row: epistemic + depth + sources */}
      <div className="flex items-center justify-between text-[8px] text-muted-foreground">
        {arg.epistemic_status && (
          <span
            className="font-mono capitalize"
            style={{ color: `var(--${arg.epistemic_status})` }}
          >
            {arg.epistemic_status}
          </span>
        )}
        <span className="font-mono">
          d={arg.tag.derivation_depth} | t={arg.tag.trust_score.toFixed(1)}
        </span>
        {(arg.tag.source_ids?.length ?? 0) > 0 && (
          <span className="font-mono opacity-60">
            {arg.tag.source_ids.length} src
          </span>
        )}
      </div>

      {/* Vyapti reference */}
      {arg.vyapti_id && (
        <div className="text-[8px] font-mono truncate" style={{ color: "var(--prov-vyapti)" }}>
          via {arg.vyapti_id}
        </div>
      )}

      <Handle type="source" position={Position.Top} className="!w-2 !h-2" />
    </div>
  );
});
