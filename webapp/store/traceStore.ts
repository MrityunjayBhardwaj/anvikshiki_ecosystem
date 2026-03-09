import { create } from "zustand";
import type { TraceStage } from "@/lib/types";

const STAGE_DEFS: { id: TraceStage["id"]; label: string }[] = [
  { id: "stage:grounding",   label: "Predicate Grounding" },
  { id: "stage:coverage",    label: "Coverage Analysis" },
  { id: "stage:compilation", label: "KB Compilation (T2b)" },
  { id: "stage:extension",   label: "Argumentation Extension" },
  { id: "stage:synthesis",   label: "Response Synthesis" },
];

function freshStages(): TraceStage[] {
  return STAGE_DEFS.map((d) => ({ ...d, status: "pending" }));
}

interface TraceState {
  stages: TraceStage[];
  open: boolean;
  setOpen: (v: boolean) => void;
  startRun: () => void;
  markRunning: (stageId: string) => void;
  markDone: (stageId: string, data?: Record<string, unknown>, durationMs?: number) => void;
  markError: (stageId: string, msg: string) => void;
  reset: () => void;
}

export const useTraceStore = create<TraceState>((set) => ({
  stages: freshStages(),
  open: false,
  setOpen: (open) => set({ open }),
  startRun: () => set({ stages: freshStages(), open: true }),
  markRunning: (stageId) =>
    set((s) => ({
      stages: s.stages.map((st) =>
        st.id === stageId ? { ...st, status: "running" } : st
      ),
    })),
  markDone: (stageId, data, durationMs) =>
    set((s) => ({
      stages: s.stages.map((st) =>
        st.id === stageId ? { ...st, status: "done", data, durationMs } : st
      ),
    })),
  markError: (stageId, msg) =>
    set((s) => ({
      stages: s.stages.map((st) =>
        st.id === stageId ? { ...st, status: "error", data: { message: msg } } : st
      ),
    })),
  reset: () => set({ stages: freshStages(), open: false }),
}));
