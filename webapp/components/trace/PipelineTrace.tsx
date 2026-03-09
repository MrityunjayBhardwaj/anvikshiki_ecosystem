"use client";

import { CheckCircle2, Circle, Loader2, AlertCircle, ChevronRight } from "lucide-react";
import { Button } from "@/components/ui/button";
import {
  Sheet,
  SheetContent,
  SheetHeader,
  SheetTitle,
  SheetTrigger,
} from "@/components/ui/sheet";
import { Badge } from "@/components/ui/badge";
import { ScrollArea } from "@/components/ui/scroll-area";
import { useTraceStore } from "@/store/traceStore";
import type { TraceStage } from "@/lib/types";

function StageRow({ stage }: { stage: TraceStage }) {
  const icon =
    stage.status === "done" ? (
      <CheckCircle2 className="w-3.5 h-3.5 text-green-500 shrink-0" />
    ) : stage.status === "running" ? (
      <Loader2 className="w-3.5 h-3.5 animate-spin text-blue-400 shrink-0" />
    ) : stage.status === "error" ? (
      <AlertCircle className="w-3.5 h-3.5 text-destructive shrink-0" />
    ) : (
      <Circle className="w-3.5 h-3.5 text-muted-foreground/40 shrink-0" />
    );

  return (
    <div className="flex items-start gap-2 py-2">
      <div className="mt-0.5">{icon}</div>
      <div className="flex-1 min-w-0">
        <div className="flex items-center justify-between gap-2">
          <span
            className={`text-xs font-medium ${
              stage.status === "pending" ? "text-muted-foreground" : "text-foreground"
            }`}
          >
            {stage.label}
          </span>
          {stage.durationMs != null && (
            <span className="text-[10px] font-mono text-muted-foreground shrink-0">
              {stage.durationMs}ms
            </span>
          )}
        </div>

        {/* Stage data preview */}
        {stage.data != null && stage.status !== "error" && (
          <div className="mt-1 space-y-0.5">
            {Object.entries(stage.data).map(([k, v]) => {
              const display = v === null || v === undefined
                ? "null"
                : typeof v === "object"
                ? JSON.stringify(v).slice(0, 60)
                : String(v).slice(0, 60);
              return (
                <div key={k} className="flex gap-1 text-[10px] font-mono text-muted-foreground">
                  <span className="shrink-0 text-muted-foreground/60">{k}:</span>
                  <span className="truncate">{display}</span>
                </div>
              );
            })}
          </div>
        )}

        {stage.status === "error" && stage.data?.message != null && (
          <p className="text-[10px] text-destructive mt-0.5 font-mono">
            {String(stage.data.message)}
          </p>
        )}
      </div>
    </div>
  );
}

function StatusDots({ stages }: { stages: TraceStage[] }) {
  return (
    <div className="flex gap-1 items-center">
      {stages.map((s) => (
        <div
          key={s.id}
          className={`w-1.5 h-1.5 rounded-full ${
            s.status === "done"
              ? "bg-green-500"
              : s.status === "running"
              ? "bg-blue-400 animate-pulse"
              : s.status === "error"
              ? "bg-destructive"
              : "bg-muted-foreground/30"
          }`}
        />
      ))}
    </div>
  );
}

export function PipelineTrace() {
  const { stages, open, setOpen } = useTraceStore();
  const doneCount = stages.filter((s) => s.status === "done").length;
  const hasError = stages.some((s) => s.status === "error");
  const isRunning = stages.some((s) => s.status === "running");

  return (
    <Sheet open={open} onOpenChange={setOpen}>
      <SheetTrigger asChild>
        <Button
          variant="ghost"
          size="sm"
          className="w-full justify-between text-xs h-7 px-2"
        >
          <div className="flex items-center gap-2">
            <span className="text-muted-foreground">Pipeline Trace</span>
            <StatusDots stages={stages} />
          </div>
          <div className="flex items-center gap-1.5">
            {isRunning && (
              <Badge variant="secondary" className="text-[10px] h-4">
                running
              </Badge>
            )}
            {!isRunning && doneCount > 0 && (
              <Badge
                variant={hasError ? "destructive" : "secondary"}
                className="text-[10px] h-4 font-mono"
              >
                {doneCount}/5
              </Badge>
            )}
            <ChevronRight className="w-3 h-3 text-muted-foreground" />
          </div>
        </Button>
      </SheetTrigger>

      <SheetContent side="right" className="w-96 p-0">
        <SheetHeader className="px-4 py-3 border-b">
          <SheetTitle className="text-sm">Pipeline Trace</SheetTitle>
        </SheetHeader>

        <ScrollArea className="h-[calc(100vh-56px)]">
          <div className="px-4 py-2 divide-y divide-border">
            {stages.map((stage) => (
              <StageRow key={stage.id} stage={stage} />
            ))}
          </div>
        </ScrollArea>
      </SheetContent>
    </Sheet>
  );
}
