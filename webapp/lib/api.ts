import { EngineResultSchema, type EngineResult, type KBInfo, type StageEvent } from "./types";

const BASE = "";  // rewrites proxy /api and /kb to localhost:8000

// ── Health ─────────────────────────────────────────────────────────────────

export async function checkHealth(): Promise<{ engine_loaded: boolean; kb_name: string | null }> {
  const res = await fetch(`${BASE}/health`);
  if (!res.ok) throw new Error("Backend unreachable");
  return res.json();
}

// ── KB management ──────────────────────────────────────────────────────────

export async function loadKB(kb_yaml_path: string, guide_dir?: string): Promise<KBInfo> {
  const res = await fetch(`${BASE}/kb/load`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ kb_yaml_path, guide_dir }),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(err.detail ?? "Failed to load KB");
  }
  return res.json();
}

export async function inspectKB(): Promise<KBInfo> {
  const res = await fetch(`${BASE}/kb/inspect`);
  if (!res.ok) throw new Error("Failed to inspect KB");
  return res.json();
}

// ── Synchronous query ──────────────────────────────────────────────────────

export async function runQuery(query: string, mode = "full"): Promise<EngineResult> {
  const res = await fetch(`${BASE}/api/query`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ query, mode }),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(err.detail ?? "Query failed");
  }
  const raw = await res.json();
  return EngineResultSchema.parse(raw);
}

// ── SSE streaming query ────────────────────────────────────────────────────

export function streamQuery(
  query: string,
  mode: string,
  onEvent: (event: StageEvent) => void,
  onComplete: (result: EngineResult) => void,
  onError: (message: string) => void,
): () => void {
  const params = new URLSearchParams({ query, mode });
  const url = `${BASE}/api/query/stream?${params}`;
  const es = new EventSource(url);

  const stages = ["stage:grounding", "stage:coverage", "stage:compilation", "stage:extension", "stage:synthesis"];

  for (const stage of stages) {
    es.addEventListener(stage, (e: MessageEvent) => {
      try {
        onEvent({ type: stage as StageEvent["type"], data: JSON.parse(e.data) });
      } catch {}
    });
  }

  es.addEventListener("complete", (e: MessageEvent) => {
    try {
      const raw = JSON.parse(e.data);
      const result = EngineResultSchema.parse(raw);
      onComplete(result);
    } catch (err) {
      onError(String(err));
    }
    es.close();
  });

  es.addEventListener("error", (e: MessageEvent) => {
    try {
      const { message } = JSON.parse(e.data);
      onError(message);
    } catch {
      onError("Stream error");
    }
    es.close();
  });

  es.onerror = () => {
    onError("EventSource connection failed");
    es.close();
  };

  return () => es.close();
}
