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
              <TableHead className="text-[10px] w-20">Belief</TableHead>
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
                          b={arg.tag.belief.toFixed(3)} d=
                          {arg.tag.disbelief.toFixed(3)} u=
                          {arg.tag.uncertainty.toFixed(3)}
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
                    <div className="font-mono text-[10px] text-muted-foreground">
                      {arg.tag.belief.toFixed(2)}
                    </div>
                    <div
                      className="h-0.5 rounded-full mt-0.5 bg-current"
                      style={{
                        width: `${arg.tag.belief * 100}%`,
                        color: "var(--label-in)",
                      }}
                    />
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
