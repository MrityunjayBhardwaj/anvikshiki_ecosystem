import { z } from "zod";

// ── Enums ──────────────────────────────────────────────────────────────────

export const PramanaType = z.enum(["UPAMANA", "SABDA", "ANUMANA", "PRATYAKSA"]);
export const EpistemicStatus = z.enum(["established", "hypothesis", "provisional", "open", "contested"]);
export const Label = z.enum(["in", "out", "undecided"]);
export const CoverageDecision = z.enum(["FULL", "PARTIAL", "DECLINE"]);
export const GroundingMode = z.enum(["minimal", "partial", "full"]);
export const AttackType = z.enum(["rebuttal", "undercutting", "undermining"]);
export const RuleType = z.enum(["strict", "defeasible"]);

// ── ProvenanceTag ──────────────────────────────────────────────────────────

export const ProvenanceTagSchema = z.object({
  belief: z.number(),
  disbelief: z.number(),
  uncertainty: z.number(),
  pramana_type: PramanaType,
  source_ids: z.array(z.string()),
  trust_score: z.number(),
  decay_factor: z.number(),
  derivation_depth: z.number(),
  timestamp: z.string().optional().nullable(),
});

// ── Argumentation graph ────────────────────────────────────────────────────

export const ArgumentNodeSchema = z.object({
  id: z.string(),
  conclusion: z.string(),
  rule_type: RuleType,
  label: Label,
  epistemic_status: EpistemicStatus.nullable(),
  tag: ProvenanceTagSchema,
  premises: z.array(z.string()),
  vyapti_id: z.string().optional().nullable(),
});

export const AttackEdgeSchema = z.object({
  id: z.string(),
  attacker: z.string(),
  target: z.string(),
  attack_type: AttackType,
  hetvabhasa: z.string().nullable(),
  specificity_weight: z.number().optional().nullable(),
});

// ── Result sub-schemas ─────────────────────────────────────────────────────

export const ProvenanceEntrySchema = z.object({
  sources: z.array(z.string()),
  pramana: PramanaType,
  derivation_depth: z.number(),
  trust: z.number(),
  decay: z.number(),
});

export const UncertaintyEntrySchema = z.object({
  total_confidence: z.number(),
  epistemic: z.object({ status: EpistemicStatus }),
  aleatoric: z.number().optional().nullable(),
  model: z.number().optional().nullable(),
});

export const CoverageResultSchema = z.object({
  coverage_ratio: z.number(),
  matched_predicates: z.array(z.string()),
  unmatched_predicates: z.array(z.string()),
  match_details: z.record(z.string(), z.string()),
  relevant_vyaptis: z.array(z.string()),
  decision: CoverageDecision,
});

export const ViolationSchema = z.object({
  hetvabhasa: z.string().nullable(),
  type: AttackType,
  attacker: z.string(),
  target: z.string(),
  target_conclusion: z.string(),
});

export const AugmentationSchema = z.object({
  augmented: z.boolean(),
  reason: z.string(),
  framework_score: z.number(),
  new_vyapti_count: z.number(),
  warnings: z.array(z.string()),
});

export const ContestationSchema = z.object({
  mode: z.string(),
  open_questions: z.array(z.string()),
  suggested_evidence: z.array(z.string()),
});

// ── Engine result (full) ───────────────────────────────────────────────────

export const EngineResultSchema = z.object({
  response: z.string(),
  sources: z.array(z.string()),
  uncertainty: z.record(z.string(), UncertaintyEntrySchema),
  provenance: z.record(z.string(), ProvenanceEntrySchema),
  violations: z.array(ViolationSchema),
  grounding_confidence: z.number(),
  extension_size: z.number(),
  coverage: CoverageResultSchema.nullable(),
  augmentation: AugmentationSchema.nullable(),
  contestation: ContestationSchema.nullable(),
  arguments: z.record(z.string(), ArgumentNodeSchema),
  attacks: z.array(AttackEdgeSchema),
  labels: z.record(z.string(), Label),
});

// ── Inferred types ─────────────────────────────────────────────────────────

export type EngineResult = z.infer<typeof EngineResultSchema>;
export type ArgumentNode = z.infer<typeof ArgumentNodeSchema>;
export type AttackEdge = z.infer<typeof AttackEdgeSchema>;
export type ProvenanceTag = z.infer<typeof ProvenanceTagSchema>;
export type CoverageResult = z.infer<typeof CoverageResultSchema>;
export type Violation = z.infer<typeof ViolationSchema>;

// ── SSE stage events ───────────────────────────────────────────────────────

export interface StageEvent {
  type: "stage:grounding" | "stage:coverage" | "stage:compilation" | "stage:extension" | "stage:synthesis" | "complete" | "error";
  data: Record<string, unknown>;
}

export type TraceStage = {
  id: string;
  label: string;
  status: "pending" | "running" | "done" | "error";
  data?: Record<string, unknown>;
  durationMs?: number;
};

// ── KB info ────────────────────────────────────────────────────────────────

export interface KBInfo {
  kb_name: string;
  vyapti_count: number;
  argument_count: number;
  loaded: boolean;
}

// ── Query history entry ────────────────────────────────────────────────────

export interface HistoryEntry {
  id: string;
  query: string;
  result: EngineResult;
  mode: string;
  timestamp: string;
}
