"use client";

import { AlertCircle, BookOpen, CheckCircle2 } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Skeleton } from "@/components/ui/skeleton";
import { useQueryStore } from "@/store/queryStore";

export function ResponseCard() {
  const { result, running, error } = useQueryStore();

  if (error) {
    return (
      <Card className="border-destructive">
        <CardHeader className="pb-2">
          <div className="flex items-center gap-1.5 text-destructive">
            <AlertCircle className="w-3.5 h-3.5" />
            <CardTitle className="text-sm">Error</CardTitle>
          </div>
        </CardHeader>
        <CardContent>
          <p className="text-xs font-mono text-destructive">{error}</p>
        </CardContent>
      </Card>
    );
  }

  if (running && !result) {
    return (
      <Card>
        <CardHeader className="pb-2">
          <CardTitle className="text-sm text-muted-foreground">
            Synthesizing...
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-2">
          <Skeleton className="h-3 w-full" />
          <Skeleton className="h-3 w-4/5" />
          <Skeleton className="h-3 w-3/4" />
          <Skeleton className="h-3 w-full" />
        </CardContent>
      </Card>
    );
  }

  if (!result) return null;

  const confidence = (result.grounding_confidence * 100).toFixed(0);
  const coverage = result.coverage;

  return (
    <Card>
      <CardHeader className="pb-2">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-1.5">
            <CheckCircle2 className="w-3.5 h-3.5 text-green-500" />
            <CardTitle className="text-sm">Response</CardTitle>
          </div>
          <div className="flex items-center gap-1">
            <Badge variant="secondary" className="text-[10px] font-mono">
              {confidence}% conf
            </Badge>
            {coverage && (
              <Badge
                variant="outline"
                className="text-[10px] font-mono"
                style={{
                  color: `var(--coverage-${coverage.decision.toLowerCase()})`,
                  borderColor: `var(--coverage-${coverage.decision.toLowerCase()})`,
                }}
              >
                {coverage.decision}
              </Badge>
            )}
          </div>
        </div>
      </CardHeader>
      <CardContent className="space-y-3">
        <ScrollArea className="max-h-64">
          <p className="text-sm leading-relaxed whitespace-pre-wrap">
            {result.response}
          </p>
        </ScrollArea>

        {/* Sources */}
        {result.sources.length > 0 && (
          <div className="border-t pt-2">
            <div className="flex items-center gap-1 text-xs text-muted-foreground mb-1.5">
              <BookOpen className="w-3 h-3" />
              Sources
            </div>
            <div className="space-y-0.5">
              {result.sources.map((s, i) => (
                <p key={i} className="text-[10px] font-mono text-muted-foreground truncate">
                  {s}
                </p>
              ))}
            </div>
          </div>
        )}

        {/* Violations */}
        {result.violations.length > 0 && (
          <div className="border-t pt-2">
            <p className="text-xs text-muted-foreground mb-1.5">
              Hetvābhāsa violations ({result.violations.length})
            </p>
            {result.violations.map((v, i) => (
              <div key={i} className="text-[10px] font-mono text-destructive/80 truncate">
                {v.hetvabhasa ?? v.type}: {v.target_conclusion}
              </div>
            ))}
          </div>
        )}
      </CardContent>
    </Card>
  );
}
