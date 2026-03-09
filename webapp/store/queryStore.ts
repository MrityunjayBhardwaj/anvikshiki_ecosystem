import { create } from "zustand";
import type { EngineResult, HistoryEntry } from "@/lib/types";

interface QueryState {
  query: string;
  mode: "minimal" | "partial" | "full";
  running: boolean;
  result: EngineResult | null;
  error: string | null;
  selectedNodeId: string | null;
  history: HistoryEntry[];

  setQuery: (q: string) => void;
  setMode: (m: "minimal" | "partial" | "full") => void;
  setRunning: (v: boolean) => void;
  setResult: (r: EngineResult | null) => void;
  setError: (e: string | null) => void;
  setSelectedNode: (id: string | null) => void;
  addHistory: (entry: HistoryEntry) => void;
  replayHistory: (entry: HistoryEntry) => void;
  reset: () => void;
}

export const useQueryStore = create<QueryState>((set) => ({
  query: "",
  mode: "partial",
  running: false,
  result: null,
  error: null,
  selectedNodeId: null,
  history: [],

  setQuery: (query) => set({ query }),
  setMode: (mode) => set({ mode }),
  setRunning: (running) => set({ running }),
  setResult: (result) => set({ result, error: null }),
  setError: (error) => set({ error, running: false }),
  setSelectedNode: (selectedNodeId) => set({ selectedNodeId }),
  addHistory: (entry) =>
    set((s) => ({ history: [entry, ...s.history].slice(0, 50) })),
  replayHistory: (entry) =>
    set({ query: entry.query, result: entry.result, mode: entry.mode as never }),
  reset: () => set({ query: "", result: null, error: null, running: false }),
}));
