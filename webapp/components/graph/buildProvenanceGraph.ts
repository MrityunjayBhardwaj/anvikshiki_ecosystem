/**
 * Transforms an EngineResult into a multi-layer provenance chain graph.
 *
 * Node layers (bottom → top):
 *   0: Sources (references backing claims)
 *   1: Premise arguments (grounded base facts)
 *   2: Vyaptis (rules used in derivation)
 *   3: Derived arguments (conclusions)
 *
 * Edge types:
 *   - derivation: premise → derived argument (support chain)
 *   - rule:       vyapti → derived argument (rule application)
 *   - source:     source → argument (provenance reference)
 *   - attack:     attacker → target (ASPIC+ defeat)
 */

import type { Node, Edge } from "@xyflow/react";
import type { EngineResult, ArgumentNode as ArgNodeType } from "@/lib/types";

// ── Node data types ─────────────────────────────────────────────────────────

export interface SourceNodeData {
  sourceId: string;
  referencedBy: number; // how many arguments cite this source
}

export interface VyaptiNodeData {
  vyaptiId: string;
  usedBy: number; // how many arguments use this rule
}

export interface ArgChainNodeData {
  arg: ArgNodeType;
  isPremise: boolean;
  chainDepth: number; // distance from a root conclusion
}

// ── Graph depth levels ──────────────────────────────────────────────────────

export type DepthLevel = 1 | 2 | 3 | 4;

export const DEPTH_LABELS: Record<DepthLevel, string> = {
  1: "Conclusions",
  2: "Arguments",
  3: "Rules & Sources",
  4: "Full Chain",
};

// ── Builder ─────────────────────────────────────────────────────────────────

export interface ProvenanceGraph {
  nodes: Node[];
  edges: Edge[];
  stats: {
    sourceCount: number;
    vyaptiCount: number;
    premiseCount: number;
    conclusionCount: number;
    derivationEdges: number;
    attackEdges: number;
  };
}

export function buildProvenanceGraph(
  result: EngineResult,
  depth: DepthLevel = 4,
): ProvenanceGraph {
  const args = Object.values(result.arguments) as ArgNodeType[];

  // ── Index: conclusion string → argument IDs ─────────────────────────────
  const conclusionIndex = new Map<string, string[]>();
  for (const arg of args) {
    const list = conclusionIndex.get(arg.conclusion) ?? [];
    list.push(arg.id);
    conclusionIndex.set(arg.conclusion, list);
  }

  // ── Classify arguments ──────────────────────────────────────────────────
  const premises: ArgNodeType[] = [];
  const derived: ArgNodeType[] = [];
  for (const arg of args) {
    if (arg.vyapti_id) {
      derived.push(arg);
    } else {
      premises.push(arg);
    }
  }

  // ── Collect unique sources and vyaptis ──────────────────────────────────
  const sourceRefCount = new Map<string, number>();
  for (const arg of args) {
    for (const sid of arg.tag.source_ids ?? []) {
      sourceRefCount.set(sid, (sourceRefCount.get(sid) ?? 0) + 1);
    }
  }

  const vyaptiUseCount = new Map<string, number>();
  for (const arg of derived) {
    if (arg.vyapti_id) {
      vyaptiUseCount.set(
        arg.vyapti_id,
        (vyaptiUseCount.get(arg.vyapti_id) ?? 0) + 1,
      );
    }
  }

  // ── Compute chain depth per argument (BFS from conclusions) ─────────────
  // "depth" here = distance from a leaf conclusion (for layout ranking)
  const chainDepth = new Map<string, number>();
  // derived conclusions start at depth 0, their premises at depth 1, etc.
  for (const arg of derived) chainDepth.set(arg.id, 0);
  for (const arg of premises) chainDepth.set(arg.id, 1);

  // ── Build all nodes ─────────────────────────────────────────────────────
  const allNodes: Node[] = [];
  const allEdges: Edge[] = [];

  // Argument nodes (always built; filtered by depth later)
  for (const arg of args) {
    const isPremise = !arg.vyapti_id;
    allNodes.push({
      id: arg.id,
      type: "provenanceArg",
      position: { x: 0, y: 0 },
      data: {
        arg,
        isPremise,
        chainDepth: chainDepth.get(arg.id) ?? 0,
      } satisfies ArgChainNodeData,
    });
  }

  // Vyapti nodes
  for (const [vid, count] of vyaptiUseCount) {
    allNodes.push({
      id: `vyapti:${vid}`,
      type: "vyapti",
      position: { x: 0, y: 0 },
      data: { vyaptiId: vid, usedBy: count } satisfies VyaptiNodeData,
    });
  }

  // Source nodes
  for (const [sid, count] of sourceRefCount) {
    allNodes.push({
      id: `src:${sid}`,
      type: "source",
      position: { x: 0, y: 0 },
      data: { sourceId: sid, referencedBy: count } satisfies SourceNodeData,
    });
  }

  // ── Build all edges ─────────────────────────────────────────────────────

  let derivEdgeCount = 0;

  // Derivation edges: find premise arguments matching each derived arg's premises
  for (const arg of derived) {
    for (const premStr of arg.premises ?? []) {
      const premArgIds = conclusionIndex.get(premStr) ?? [];
      for (const premArgId of premArgIds) {
        allEdges.push({
          id: `deriv:${premArgId}-${arg.id}`,
          source: premArgId,
          target: arg.id,
          type: "derivation",
          data: { edgeKind: "derivation" },
        });
        derivEdgeCount++;
      }
    }

    // Vyapti → derived argument (rule application edge)
    if (arg.vyapti_id) {
      allEdges.push({
        id: `rule:${arg.vyapti_id}-${arg.id}`,
        source: `vyapti:${arg.vyapti_id}`,
        target: arg.id,
        type: "derivation",
        data: { edgeKind: "rule" },
      });
    }
  }

  // Source → argument edges
  for (const arg of args) {
    for (const sid of arg.tag.source_ids ?? []) {
      allEdges.push({
        id: `prov:${sid}-${arg.id}`,
        source: `src:${sid}`,
        target: arg.id,
        type: "derivation",
        data: { edgeKind: "source" },
      });
    }
  }

  // Attack edges
  for (const atk of result.attacks) {
    allEdges.push({
      id: `atk:${atk.id}`,
      source: atk.attacker,
      target: atk.target,
      type: "attack",
      data: { attack: atk },
      animated: atk.attack_type === "rebutting",
    });
  }

  // ── Filter by depth ─────────────────────────────────────────────────────
  const visible = filterByDepth(allNodes, allEdges, depth, result);

  return {
    ...visible,
    stats: {
      sourceCount: sourceRefCount.size,
      vyaptiCount: vyaptiUseCount.size,
      premiseCount: premises.length,
      conclusionCount: derived.length,
      derivationEdges: derivEdgeCount,
      attackEdges: result.attacks.length,
    },
  };
}

// ── Depth filtering ─────────────────────────────────────────────────────────

function filterByDepth(
  allNodes: Node[],
  allEdges: Edge[],
  depth: DepthLevel,
  result: EngineResult,
): { nodes: Node[]; edges: Edge[] } {
  const visibleIds = new Set<string>();

  const args = Object.values(result.arguments);

  if (depth >= 1) {
    // Show IN conclusions only
    for (const arg of args) {
      if (arg.label === "in") visibleIds.add(arg.id);
    }
  }

  if (depth >= 2) {
    // Show ALL arguments (premises + derived + attacked)
    for (const arg of args) {
      visibleIds.add(arg.id);
    }
  }

  if (depth >= 3) {
    // Show vyaptis
    for (const arg of args) {
      if (arg.vyapti_id) visibleIds.add(`vyapti:${arg.vyapti_id}`);
    }
  }

  if (depth >= 4) {
    // Show sources
    for (const arg of args) {
      for (const sid of arg.tag.source_ids ?? []) {
        visibleIds.add(`src:${sid}`);
      }
    }
  }

  const nodes = allNodes.filter((n) => visibleIds.has(n.id));
  const edges = allEdges.filter(
    (e) => visibleIds.has(e.source) && visibleIds.has(e.target),
  );

  return { nodes, edges };
}

// ── Chain highlighting ──────────────────────────────────────────────────────

/** Given a selected node ID, find all ancestor + descendant IDs in the chain */
export function getChainIds(
  nodeId: string,
  edges: Edge[],
): { nodeIds: Set<string>; edgeIds: Set<string> } {
  const nodeIds = new Set<string>([nodeId]);
  const edgeIds = new Set<string>();

  // Adjacency: target → sources (ancestors) and source → targets (descendants)
  const parentOf = new Map<string, { source: string; edgeId: string }[]>();
  const childOf = new Map<string, { target: string; edgeId: string }[]>();
  for (const e of edges) {
    const pList = parentOf.get(e.target) ?? [];
    pList.push({ source: e.source, edgeId: e.id });
    parentOf.set(e.target, pList);

    const cList = childOf.get(e.source) ?? [];
    cList.push({ target: e.target, edgeId: e.id });
    childOf.set(e.source, cList);
  }

  // BFS ancestors (walk source edges backward)
  const queue: string[] = [nodeId];
  while (queue.length > 0) {
    const current = queue.shift()!;
    for (const { source, edgeId } of parentOf.get(current) ?? []) {
      edgeIds.add(edgeId);
      if (!nodeIds.has(source)) {
        nodeIds.add(source);
        queue.push(source);
      }
    }
  }

  // BFS descendants (walk target edges forward)
  const queue2: string[] = [nodeId];
  const visited = new Set<string>([nodeId]);
  while (queue2.length > 0) {
    const current = queue2.shift()!;
    for (const { target, edgeId } of childOf.get(current) ?? []) {
      edgeIds.add(edgeId);
      if (!visited.has(target)) {
        visited.add(target);
        nodeIds.add(target);
        queue2.push(target);
      }
    }
  }

  return { nodeIds, edgeIds };
}
