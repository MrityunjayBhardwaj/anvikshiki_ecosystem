"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { FolderOpen, Loader2, CheckCircle2 } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { useKBStore } from "@/store/kbStore";
import { loadKB } from "@/lib/api";
import { toast } from "sonner";

const EXAMPLE_KBS = [
  {
    label: "Business Expert",
    path: "anvikshiki_v4/knowledge_bases/business_expert_kb.yaml",
  },
  {
    label: "Philosophy",
    path: "anvikshiki_v4/knowledge_bases/philosophy_kb.yaml",
  },
];

export function KBLoader() {
  const router = useRouter();
  const { kb, loading, setLoading, setKB, setError } = useKBStore();
  const [path, setPath] = useState("");

  async function handleLoad(kbPath: string) {
    setLoading(true);
    try {
      const info = await loadKB(kbPath);
      setKB(info);
      toast.success(`Loaded: ${info.kb_name}`, {
        description: `${info.vyapti_count} vyāptis · ${info.argument_count} arguments`,
      });
      router.push("/studio");
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : "Failed to load KB";
      setError(msg);
      toast.error("Failed to load KB", { description: msg });
    }
  }

  return (
    <Card>
      <CardHeader>
        <div className="flex items-center justify-between">
          <CardTitle className="text-base">Load Knowledge Base</CardTitle>
          {kb && (
            <Badge variant="outline" className="gap-1 text-xs font-mono">
              <CheckCircle2 className="w-3 h-3 text-green-500" />
              {kb.kb_name}
            </Badge>
          )}
        </div>
        <CardDescription className="text-xs">
          Point to a{" "}
          <code className="font-mono text-xs bg-muted px-1 rounded">.yaml</code>{" "}
          KB file on the backend filesystem.
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-4">
        {/* Quick-select examples */}
        <div className="flex flex-wrap gap-2">
          {EXAMPLE_KBS.map((ex) => (
            <Button
              key={ex.path}
              variant="outline"
              size="sm"
              className="text-xs h-7"
              disabled={loading}
              onClick={() => handleLoad(ex.path)}
            >
              {ex.label}
            </Button>
          ))}
        </div>

        {/* Custom path */}
        <div className="space-y-1.5">
          <Label htmlFor="kb-path" className="text-xs">
            Custom path
          </Label>
          <div className="flex gap-2">
            <Input
              id="kb-path"
              placeholder="path/to/kb.yaml"
              value={path}
              onChange={(e) => setPath(e.target.value)}
              className="font-mono text-xs h-8"
              disabled={loading}
              onKeyDown={(e) => {
                if (e.key === "Enter" && path.trim()) handleLoad(path.trim());
              }}
            />
            <Button
              size="sm"
              className="h-8 gap-1.5"
              disabled={loading || !path.trim()}
              onClick={() => handleLoad(path.trim())}
            >
              {loading ? (
                <Loader2 className="w-3 h-3 animate-spin" />
              ) : (
                <FolderOpen className="w-3 h-3" />
              )}
              Load
            </Button>
          </div>
        </div>

        {/* Go to studio if already loaded */}
        {kb && (
          <Button
            variant="default"
            size="sm"
            className="w-full text-xs"
            onClick={() => router.push("/studio")}
          >
            Open Query Studio →
          </Button>
        )}
      </CardContent>
    </Card>
  );
}
