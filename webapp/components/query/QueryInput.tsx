"use client";

import { useRef } from "react";
import { Send, Loader2 } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Label } from "@/components/ui/label";
import { useQueryStore } from "@/store/queryStore";
import { useTraceStore } from "@/store/traceStore";
import { streamQuery } from "@/lib/api";
import type { EngineResult, StageEvent } from "@/lib/types";
import { toast } from "sonner";

const EXAMPLE_QUERIES = [
  "How do unit economics work for a SaaS business?",
  "What makes a pricing strategy defensible?",
  "Explain the relationship between customer acquisition cost and lifetime value.",
];

export function QueryInput() {
  const { query, mode, running, setQuery, setMode, setRunning, setResult, setError, addHistory } =
    useQueryStore();
  const trace = useTraceStore();
  const abortRef = useRef<(() => void) | null>(null);

  function handleSubmit() {
    if (!query.trim() || running) return;
    setRunning(true);
    trace.startRun();

    const stageOrder = [
      "stage:grounding",
      "stage:coverage",
      "stage:compilation",
      "stage:extension",
      "stage:synthesis",
    ];
    let stageIdx = 0;

    function onEvent(event: StageEvent) {
      if (stageIdx < stageOrder.length) {
        trace.markDone(stageOrder[stageIdx], event.data);
        stageIdx++;
        if (stageIdx < stageOrder.length) {
          trace.markRunning(stageOrder[stageIdx]);
        }
      }
    }

    function onComplete(result: EngineResult) {
      setResult(result);
      setRunning(false);
      addHistory({
        id: crypto.randomUUID(),
        query,
        result,
        mode,
        timestamp: new Date().toISOString(),
      });
      toast.success("Query complete", {
        description: `Confidence: ${(result.grounding_confidence * 100).toFixed(0)}% · ${result.extension_size} args`,
      });
    }

    function onError(message: string) {
      setError(message);
      setRunning(false);
      toast.error("Query failed", { description: message });
    }

    trace.markRunning(stageOrder[0]);
    abortRef.current = streamQuery(query, mode, onEvent, onComplete, onError);
  }

  function handleStop() {
    abortRef.current?.();
    setRunning(false);
    toast.info("Query stopped");
  }

  return (
    <div className="space-y-2">
      {/* Mode selector */}
      <div className="flex items-center justify-between">
        <Label className="text-xs font-medium text-muted-foreground">
          Grounding mode
        </Label>
        <Select value={mode} onValueChange={(v) => setMode(v as typeof mode)}>
          <SelectTrigger className="h-6 w-28 text-xs">
            <SelectValue />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="minimal" className="text-xs">
              Minimal (1 call)
            </SelectItem>
            <SelectItem value="partial" className="text-xs">
              Partial (N=3)
            </SelectItem>
            <SelectItem value="full" className="text-xs">
              Full (N=5 + RT)
            </SelectItem>
          </SelectContent>
        </Select>
      </div>

      {/* Textarea */}
      <Textarea
        placeholder="Ask something about the loaded knowledge base..."
        value={query}
        onChange={(e) => setQuery(e.target.value)}
        disabled={running}
        rows={4}
        className="resize-none text-sm font-mono"
        onKeyDown={(e) => {
          if (e.key === "Enter" && (e.metaKey || e.ctrlKey)) handleSubmit();
        }}
      />

      {/* Example chips */}
      <div className="flex flex-wrap gap-1">
        {EXAMPLE_QUERIES.map((q) => (
          <button
            key={q}
            className="text-[10px] text-muted-foreground hover:text-foreground px-1.5 py-0.5 rounded border border-border hover:border-foreground/30 transition-colors truncate max-w-[140px]"
            onClick={() => setQuery(q)}
          >
            {q}
          </button>
        ))}
      </div>

      {/* Submit / Stop */}
      <div className="flex gap-2">
        <Button
          size="sm"
          className="flex-1 gap-1.5 text-xs"
          disabled={!query.trim() || running}
          onClick={handleSubmit}
        >
          {running ? (
            <Loader2 className="w-3 h-3 animate-spin" />
          ) : (
            <Send className="w-3 h-3" />
          )}
          {running ? "Running..." : "Run Query ⌘↵"}
        </Button>
        {running && (
          <Button
            size="sm"
            variant="destructive"
            className="text-xs"
            onClick={handleStop}
          >
            Stop
          </Button>
        )}
      </div>
    </div>
  );
}
