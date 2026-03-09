"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";
import { useTheme } from "next-themes";
import { Moon, Sun, Home, GitBranch } from "lucide-react";
import Link from "next/link";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Separator } from "@/components/ui/separator";
import { useKBStore } from "@/store/kbStore";

import { QueryInput } from "@/components/query/QueryInput";
import { ResponseCard } from "@/components/query/ResponseCard";
import { ProvenanceTable } from "@/components/query/ProvenanceTable";
import { CoverageIndicator } from "@/components/query/CoverageIndicator";
import { ArgumentationGraph } from "@/components/graph/ArgumentationGraph";
import { PipelineTrace } from "@/components/trace/PipelineTrace";

export default function StudioPage() {
  const router = useRouter();
  const { resolvedTheme, setTheme } = useTheme();
  const { kb } = useKBStore();

  // Redirect to home if no KB loaded
  useEffect(() => {
    if (!kb) router.replace("/");
  }, [kb, router]);

  if (!kb) return null;

  return (
    <div className="h-screen flex flex-col bg-background overflow-hidden">
      {/* Top bar */}
      <header className="border-b px-4 py-2 flex items-center justify-between shrink-0">
        <div className="flex items-center gap-3">
          <Link href="/" className="text-muted-foreground hover:text-foreground">
            <Home className="w-4 h-4" />
          </Link>
          <Separator orientation="vertical" className="h-4" />
          <div className="flex items-center gap-2">
            <div className="w-6 h-6 rounded bg-primary flex items-center justify-center text-primary-foreground font-mono text-xs font-bold">
              आ
            </div>
            <span className="font-medium text-sm tracking-tight">
              Ānvīkṣikī
            </span>
          </div>
          <Badge variant="secondary" className="text-xs font-mono gap-1">
            <GitBranch className="w-2.5 h-2.5" />
            {kb.kb_name}
          </Badge>
          <span className="text-xs text-muted-foreground font-mono">
            {kb.vyapti_count} vyāptis · {kb.argument_count} args
          </span>
        </div>

        <Button
          variant="ghost"
          size="icon"
          className="w-7 h-7"
          onClick={() => setTheme(resolvedTheme === "dark" ? "light" : "dark")}
        >
          {resolvedTheme === "dark" ? (
            <Sun className="w-3.5 h-3.5" />
          ) : (
            <Moon className="w-3.5 h-3.5" />
          )}
        </Button>
      </header>

      {/* Three-column body */}
      <div className="flex-1 flex overflow-hidden">
        {/* Left — Query + Response */}
        <aside className="w-80 shrink-0 border-r flex flex-col overflow-hidden">
          <div className="flex-1 overflow-y-auto p-3 space-y-3">
            <QueryInput />
            <CoverageIndicator />
            <ResponseCard />
          </div>
          <div className="border-t p-2 shrink-0">
            <PipelineTrace />
          </div>
        </aside>

        {/* Center — Argumentation graph */}
        <main className="flex-1 overflow-hidden">
          <ArgumentationGraph />
        </main>

        {/* Right — Provenance + details */}
        <aside className="w-80 shrink-0 border-l overflow-y-auto p-3">
          <ProvenanceTable />
        </aside>
      </div>
    </div>
  );
}
