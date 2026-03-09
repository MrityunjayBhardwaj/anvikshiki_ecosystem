"use client";

import { Progress } from "@/components/ui/progress";
import { Badge } from "@/components/ui/badge";
import { useQueryStore } from "@/store/queryStore";

const DECISION_COLOR: Record<string, string> = {
  FULL: "var(--coverage-full)",
  PARTIAL: "var(--coverage-partial)",
  DECLINE: "var(--coverage-decline)",
};

export function CoverageIndicator() {
  const { result } = useQueryStore();
  if (!result?.coverage) return null;

  const { coverage_ratio, matched_predicates, unmatched_predicates, decision } = result.coverage;
  const pct = Math.round(coverage_ratio * 100);
  const color = DECISION_COLOR[decision] ?? "currentColor";

  return (
    <div className="space-y-1.5 p-3 rounded-lg border bg-card">
      <div className="flex items-center justify-between text-xs">
        <span className="text-muted-foreground font-medium">KB Coverage</span>
        <div className="flex items-center gap-1.5">
          <span className="font-mono font-semibold" style={{ color }}>
            {pct}%
          </span>
          <Badge
            variant="outline"
            className="text-[10px] font-mono"
            style={{ color, borderColor: color }}
          >
            {decision}
          </Badge>
        </div>
      </div>

      <Progress value={pct} className="h-1.5" />

      <div className="flex gap-3 text-[10px] font-mono text-muted-foreground">
        <span className="text-green-500">
          ✓ {matched_predicates.length} matched
        </span>
        {unmatched_predicates.length > 0 && (
          <span className="text-orange-400">
            ✗ {unmatched_predicates.length} unmatched
          </span>
        )}
      </div>
    </div>
  );
}
