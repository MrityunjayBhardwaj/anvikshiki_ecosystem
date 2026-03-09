import { create } from "zustand";
import type { KBInfo } from "@/lib/types";

interface KBState {
  kb: KBInfo | null;
  loading: boolean;
  error: string | null;
  setKB: (kb: KBInfo) => void;
  setLoading: (v: boolean) => void;
  setError: (e: string | null) => void;
  reset: () => void;
}

export const useKBStore = create<KBState>((set) => ({
  kb: null,
  loading: false,
  error: null,
  setKB: (kb) => set({ kb, loading: false, error: null }),
  setLoading: (loading) => set({ loading }),
  setError: (error) => set({ error, loading: false }),
  reset: () => set({ kb: null, loading: false, error: null }),
}));
