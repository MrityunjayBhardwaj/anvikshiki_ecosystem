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
// Uses fetch + ReadableStream instead of EventSource so Next.js rewrites
// don't buffer the response.

export function streamQuery(
  query: string,
  mode: string,
  onEvent: (event: StageEvent) => void,
  onComplete: (result: EngineResult) => void,
  onError: (message: string) => void,
): () => void {
  const ctrl = new AbortController();

  (async () => {
    try {
      const res = await fetch(
        `${BASE}/api/query/stream?${new URLSearchParams({ query, mode })}`,
        { signal: ctrl.signal },
      );

      if (!res.ok || !res.body) {
        onError(`HTTP ${res.status}: ${res.statusText}`);
        return;
      }

      const reader = res.body.getReader();
      const decoder = new TextDecoder();
      let buf = "";
      let eventName = "";
      let dataLine = "";

      while (true) {
        const { done, value } = await reader.read();
        if (done) {
          // Reaching here means neither "complete" nor "error" arrived: both
          // return early. Without this the UI would wait forever.
          onError("The stream closed before the engine sent a result");
          return;
        }

        buf += decoder.decode(value, { stream: true });
        const lines = buf.split("\n");
        buf = lines.pop() ?? "";

        for (const line of lines) {
          if (line.startsWith("event: ")) {
            eventName = line.slice(7).trim();
          } else if (line.startsWith("data: ")) {
            dataLine = line.slice(6).trim();
          } else if (line === "" && eventName) {
            try {
              const parsed = JSON.parse(dataLine);
              if (eventName === "complete") {
                onComplete(EngineResultSchema.parse(parsed));
                reader.cancel();
                return;
              } else if (eventName === "error") {
                onError(parsed.message ?? "Unknown error");
                reader.cancel();
                return;
              } else if (eventName.startsWith("stage:")) {
                onEvent({ type: eventName as StageEvent["type"], data: parsed });
              }
            } catch { /* ignore parse errors */ }
            eventName = "";
            dataLine = "";
          }
        }
      }
    } catch (err) {
      if ((err as Error).name !== "AbortError") {
        onError(String(err));
      }
    }
  })();

  return () => ctrl.abort();
}
