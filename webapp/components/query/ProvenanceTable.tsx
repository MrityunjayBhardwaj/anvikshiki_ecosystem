"use client";

import { BookOpen, Eye, Brain, MessageSquare, Ruler } from "lucide-react";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import {
  Tooltip,
  TooltipContent,
  TooltipTrigger,
} from "@/components/ui/tooltip";
import { Badge } from "@/components/ui/badge";
import { ScrollArea } from "@/components/ui/scroll-area";
import { useQueryStore } from "@/store/queryStore";
import type { ArgumentNode } from "@/lib/types";

const PRAMANA_ICON: Record<string, React.ReactNode> = {
  PRATYAKSA: <Eye className="w-3 h-3" />,
  ANUMANA: <Brain className="w-3 h-3" />,
  SABDA: <MessageSquare className="w-3 h-3" />,
  UPAMANA: <Ruler className="w-3 h-3" />,
};

const PRAMANA_COLOR: Record<string, string> = {
  PRATYAKSA: "var(--pramana-pratyaksa)",
  ANUMANA: "var(--pramana-anumana)",
  SABDA: "var(--pramana-sabda)",
  UPAMANA: "var(--pramana-upamana)",
};

// The two provenance axes, as they are named to a reader. The citation tier
// `curated` is deliberately distinct from `attributed`: both leave the status
// uncapped, but only one of them means a span was checked against a source,
// and showing a hand-authored rule as "attributed" would claim a verification
// nobody performed.
const CITATION_LABEL: Record<string, string> = {
  attributed: "span verified",
  exists: "source reachable",
  unresolved: "unverified",
  fabricated: "span not found",
  curated: "hand-authored",
};

const ORIGIN_LABEL: Record<string, string> = {
  curated: "hand-authored",
  guide_extracted: "extracted from a guide",
  hitl_promoted: "reviewer-approved",
  web_sourced: "retrieved from the web",
  llm_parametric: "model's own knowledge",
};

const BOUND_LABEL: Record<string, string> = {
  authored: "as authored",
  origin: "how it was produced",
  citation: "how well it is cited",
  asserted: "asserted premise",
};

function describeBound(bound: string): string {
  if (bound.startsWith("sub:")) {
    return `a weaker step (${bound.slice(4)})`;
  }
  return BOUND_LABEL[bound] ?? bound;
}

const STATUS_COLOR: Record<string, string> = {
  established: "var(--established)",
  hypothesis: "var(--hypothesis)",
  provisional: "var(--provisional)",
  open: "var(--open)",
  contested: "var(--contested)",
};

export function ProvenanceTable() {
  const { result, selectedNodeId, setSelectedNode } = useQueryStore();

  if (!result) {
    return (
      <div className="flex items-center justify-center h-full text-xs text-muted-foreground">
        <div className="text-center space-y-1">
          <BookOpen className="w-6 h-6 mx-auto opacity-30" />
          <p>Run a query to see provenance</p>
        </div>
      </div>
    );
  }

  const args = Object.values(result.arguments) as ArgumentNode[];
  if (args.length === 0) {
    return (
      <div className="text-xs text-muted-foreground p-4">No arguments constructed.</div>
    );
  }

  return (
    <div className="space-y-3">
      <div className="flex items-center justify-between">
        <h2 className="text-sm font-medium">Provenance</h2>
        <span className="text-xs font-mono text-muted-foreground">
          {args.length} args · {result.attacks.length} attacks
        </span>
      </div>

      <ScrollArea className="h-[calc(100vh-12rem)]">
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead className="text-[10px] w-16">ID</TableHead>
              <TableHead className="text-[10px]">Conclusion</TableHead>
              <TableHead className="text-[10px] w-10">Pramāṇa</TableHead>
              <TableHead className="text-[10px] w-16">Label</TableHead>
              <TableHead className="text-[10px] w-24">Status</TableHead>
              <TableHead className="text-[10px] w-28">Bounded by</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {args.map((arg) => {
              const isSelected = selectedNodeId === arg.id;
              const labelColor =
                arg.label === "in"
                  ? "var(--label-in)"
                  : arg.label === "out"
                  ? "var(--label-out)"
                  : "var(--label-undecided)";
              const pramana = arg.tag.pramana_type;
              const statusColor = arg.epistemic_status
                ? STATUS_COLOR[arg.epistemic_status]
                : undefined;

              return (
                <TableRow
                  key={arg.id}
                  className={`cursor-pointer transition-colors ${
                    isSelected ? "bg-accent" : "hover:bg-muted/50"
                  }`}
                  onClick={() =>
                    setSelectedNode(isSelected ? null : arg.id)
                  }
                >
                  <TableCell className="font-mono text-[10px] text-muted-foreground">
                    {arg.id.slice(0, 6)}
                  </TableCell>
                  <TableCell className="text-xs max-w-[120px]">
                    <Tooltip>
                      <TooltipTrigger className="text-left truncate block max-w-[120px]">
                        {arg.conclusion}
                      </TooltipTrigger>
                      <TooltipContent className="max-w-xs text-xs">
                        <p className="font-medium mb-1">{arg.conclusion}</p>
                        {arg.epistemic_status && (
                          <p style={{ color: statusColor }}>
                            {arg.epistemic_status}
                          </p>
                        )}
                        <p className="font-mono text-[10px] text-muted-foreground mt-1">
                          trust={arg.tag.trust_score.toFixed(3)} decay=
                          {arg.tag.decay_factor.toFixed(3)} depth=
                          {arg.tag.derivation_depth}
                        </p>
                      </TooltipContent>
                    </Tooltip>
                  </TableCell>
                  <TableCell>
                    <Tooltip>
                      <TooltipTrigger>
                        <span style={{ color: PRAMANA_COLOR[pramana] }}>
                          {PRAMANA_ICON[pramana]}
                        </span>
                      </TooltipTrigger>
                      <TooltipContent className="text-xs">{pramana}</TooltipContent>
                    </Tooltip>
                  </TableCell>
                  <TableCell>
                    <Badge
                      variant="outline"
                      className="text-[10px] font-mono uppercase"
                      style={{ color: labelColor, borderColor: labelColor }}
                    >
                      {arg.label}
                    </Badge>
                  </TableCell>
                  <TableCell>
                    <div className="font-mono text-[10px] uppercase text-muted-foreground">
                      {arg.epistemic_status ?? "—"}
                    </div>
                  </TableCell>
                  <TableCell>
                    {/*
                      Three states, not two. An empty list would say "nothing
                      constrains this"; null says the argument never recorded
                      what does. Rendering them alike is the failure this
                      column exists to avoid — a ceiling shown with no
                      explanation reads as an unbounded status.
                    */}
                    {arg.status_bound_by == null ? (
                      <span className="text-[10px] text-muted-foreground italic">
                        not recorded
                      </span>
                    ) : arg.status_bound_by.length === 0 ? (
                      <span className="text-[10px] text-muted-foreground">
                        unbounded
                      </span>
                    ) : (
                      <Tooltip>
                        <TooltipTrigger className="text-left">
                          <div className="flex flex-wrap gap-1">
                            {arg.status_bound_by.map((bound) => (
                              <Badge
                                key={bound}
                                variant="secondary"
                                className="text-[9px] font-normal px-1 py-0"
                              >
                                {describeBound(bound)}
                              </Badge>
                            ))}
                          </div>
                        </TooltipTrigger>
                        <TooltipContent className="max-w-xs text-xs space-y-1">
                          <p className="font-medium">
                            Why this is {arg.status}
                          </p>
                          {/*
                            Plural on purpose. Bounds tie routinely, and
                            saying "the" constraint would imply that lifting
                            the named one would raise the status — which is
                            false whenever another sits at the same rank.
                          */}
                          <p>
                            {arg.status_bound_by.length > 1
                              ? "Several bounds sit at this level, so lifting any one of them alone would not raise it:"
                              : "Bounded by:"}
                          </p>
                          <ul className="list-disc pl-4">
                            {arg.status_bound_by.map((bound) => (
                              <li key={bound}>{describeBound(bound)}</li>
                            ))}
                          </ul>
                          <div className="pt-1 border-t text-[10px] text-muted-foreground space-y-0.5">
                            {/*
                              Absent for an argument with no top rule. An
                              asserted premise has no origin and makes no
                              citation claim, and showing it a tier would
                              invent provenance for it.
                            */}
                            <p>
                              origin:{" "}
                              {arg.origin
                                ? ORIGIN_LABEL[arg.origin] ?? arg.origin
                                : "no rule — asserted"}
                            </p>
                            <p>
                              citation:{" "}
                              {arg.citation_tier
                                ? CITATION_LABEL[arg.citation_tier] ??
                                  arg.citation_tier
                                : "no rule — asserted"}
                            </p>
                          </div>
                        </TooltipContent>
                      </Tooltip>
                    )}
                  </TableCell>
                </TableRow>
              );
            })}
          </TableBody>
        </Table>
      </ScrollArea>
    </div>
  );
}
