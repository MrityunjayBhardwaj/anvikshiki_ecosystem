"use client";

import { useEffect, useCallback, useState, useMemo } from "react";
import {
  ReactFlow,
  Background,
  Controls,
  MiniMap,
  Panel,
  useNodesState,
  useEdgesState,
  type Node,
  type Edge,
  type NodeTypes,
  type EdgeTypes,
} from "@xyflow/react";
import "@xyflow/react/dist/style.css";
import { useTheme } from "next-themes";
import {
  Layers,
  GitBranch,
  BookOpen,
  Workflow,
  CircleDot,
  ZoomIn,
} from "lucide-react";
import { useQueryStore } from "@/store/queryStore";
import { SourceNode } from "./SourceNode";
import { VyaptiNode } from "./VyaptiNode";
import { ProvenanceArgNode } from "./ProvenanceArgNode";
import { AttackEdge as AttackEdgeComponent } from "./AttackEdge";
import { DerivationEdge } from "./DerivationEdge";
import { applyProvenanceLayout } from "./provenanceLayout";
import {
  buildProvenanceGraph,
  getChainIds,
  DEPTH_LABELS,
  type DepthLevel,
  type ProvenanceGraph,
} from "./buildProvenanceGraph";

// ── Node & edge type registries ─────────────────────────────────────────────

const nodeTypes: NodeTypes = {
  provenanceArg: ProvenanceArgNode,
  source: SourceNode,
  vyapti: VyaptiNode,
};

const edgeTypes: EdgeTypes = {
  attack: AttackEdgeComponent,
  derivation: DerivationEdge,
};

// ── SVG markers for edge arrows ─────────────────────────────────────────────

function ArrowMarkers() {
  return (
    <svg style={{ position: "absolute", width: 0, height: 0 }}>
      <defs>
        {/* Derivation arrow (green) */}
        <marker
          id="prov-arrow-derivation"
          viewBox="0 0 12 12"
          refX="10"
          refY="6"
          markerWidth="8"
          markerHeight="8"
          orient="auto-start-reverse"
        >
          <path d="M 0 0 L 12 6 L 0 12 z" fill="var(--prov-derivation)" />
        </marker>
        {/* Rule arrow (blue) */}
        <marker
          id="prov-arrow-rule"
          viewBox="0 0 12 12"
          refX="10"
          refY="6"
          markerWidth="8"
          markerHeight="8"
          orient="auto-start-reverse"
        >
          <path d="M 0 0 L 12 6 L 0 12 z" fill="var(--prov-vyapti)" />
        </marker>
        {/* Source arrow (gold) */}
        <marker
          id="prov-arrow-source"
          viewBox="0 0 12 12"
          refX="10"
          refY="6"
          markerWidth="8"
          markerHeight="8"
          orient="auto-start-reverse"
        >
          <path d="M 0 0 L 12 6 L 0 12 z" fill="var(--prov-source)" />
        </marker>
        {/* Attack arrows (reuse existing attack colors) */}
        <marker
          id="arrow-rebutting"
          viewBox="0 0 12 12"
          refX="10"
          refY="6"
          markerWidth="8"
          markerHeight="8"
          orient="auto-start-reverse"
        >
          <path d="M 0 0 L 12 6 L 0 12 z" fill="var(--attack-rebuttal)" />
        </marker>
        <marker
          id="arrow-undercutting"
          viewBox="0 0 12 12"
          refX="10"
          refY="6"
          markerWidth="8"
          markerHeight="8"
          orient="auto-start-reverse"
        >
          <path d="M 0 0 L 12 6 L 0 12 z" fill="var(--attack-undercutting)" />
        </marker>
        <marker
          id="arrow-undermining"
          viewBox="0 0 12 12"
          refX="10"
          refY="6"
          markerWidth="8"
          markerHeight="8"
          orient="auto-start-reverse"
        >
          <path d="M 0 0 L 12 6 L 0 12 z" fill="var(--attack-undermining)" />
        </marker>
      </defs>
    </svg>
  );
}

// ── Depth controls ──────────────────────────────────────────────────────────

function DepthControl({
  depth,
  onChange,
}: {
  depth: DepthLevel;
  onChange: (d: DepthLevel) => void;
}) {
  const levels: DepthLevel[] = [1, 2, 3, 4];

  return (
    <div className="flex items-center gap-2 bg-card/90 backdrop-blur border rounded-lg px-3 py-2 shadow-sm">
      <Layers className="w-3.5 h-3.5 text-muted-foreground" />
      <span className="text-[10px] font-mono text-muted-foreground uppercase tracking-wider">
        Depth
      </span>
      <div className="flex gap-0.5">
        {levels.map((d) => (
          <button
            key={d}
            onClick={() => onChange(d)}
            className={`
              px-2 py-0.5 text-[10px] font-mono rounded transition-all
              ${
                d === depth
                  ? "bg-primary text-primary-foreground"
                  : "bg-muted text-muted-foreground hover:bg-accent"
              }
            `}
            title={DEPTH_LABELS[d]}
          >
            {d}
          </button>
        ))}
      </div>
      <span className="text-[9px] text-muted-foreground ml-1">
        {DEPTH_LABELS[depth]}
      </span>
    </div>
  );
}

// ── Stats legend ────────────────────────────────────────────────────────────

function GraphLegend({
  stats,
}: {
  stats: {
    sourceCount: number;
    vyaptiCount: number;
    premiseCount: number;
    conclusionCount: number;
    derivationEdges: number;
    attackEdges: number;
  };
}) {
  return (
    <div className="flex flex-wrap gap-2 bg-card/90 backdrop-blur border rounded-lg px-3 py-2 shadow-sm text-[9px] font-mono">
      <span className="flex items-center gap-1">
        <BookOpen className="w-3 h-3" style={{ color: "var(--prov-source)" }} />
        {stats.sourceCount} sources
      </span>
      <span className="flex items-center gap-1">
        <Workflow className="w-3 h-3" style={{ color: "var(--prov-vyapti)" }} />
        {stats.vyaptiCount} rules
      </span>
      <span className="flex items-center gap-1">
        <CircleDot className="w-3 h-3" style={{ color: "var(--prov-premise)" }} />
        {stats.premiseCount} premises
      </span>
      <span className="flex items-center gap-1">
        <GitBranch className="w-3 h-3" style={{ color: "var(--prov-derived)" }} />
        {stats.conclusionCount} derived
      </span>
      <span className="text-muted-foreground">|</span>
      <span style={{ color: "var(--prov-derivation)" }}>
        {stats.derivationEdges} support
      </span>
      <span style={{ color: "var(--attack-rebuttal)" }}>
        {stats.attackEdges} attack
      </span>
    </div>
  );
}

// ── Main component ──────────────────────────────────────────────────────────

const EMPTY_STATS: ProvenanceGraph["stats"] = {
  sourceCount: 0,
  vyaptiCount: 0,
  premiseCount: 0,
  conclusionCount: 0,
  derivationEdges: 0,
  attackEdges: 0,
};

export function ProvenanceChainGraph() {
  const { result, selectedNodeId, setSelectedNode } = useQueryStore();
  const { resolvedTheme } = useTheme();

  const [nodes, setNodes, onNodesChange] = useNodesState<Node>([]);
  const [edges, setEdges, onEdgesChange] = useEdgesState<Edge>([]);
  const [depth, setDepth] = useState<DepthLevel>(3);
  // The graph is derived from the result, so it is computed during render;
  // only React Flow's own node and edge state is synchronised in an effect.
  const graph = useMemo(
    () => (result ? buildProvenanceGraph(result, depth) : null),
    [result, depth],
  );
  const graphStats = graph?.stats ?? EMPTY_STATS;

  // ── Push the built graph into React Flow ────────────────────────────────
  useEffect(() => {
    if (!graph) {
      setNodes([]);
      setEdges([]);
      return;
    }
    setNodes(applyProvenanceLayout(graph.nodes, graph.edges));
    setEdges(graph.edges);
  }, [graph, setNodes, setEdges]);

  // ── Chain highlighting ──────────────────────────────────────────────────
  const { chainNodeIds, chainEdgeIds } = useMemo(() => {
    if (!selectedNodeId || edges.length === 0) {
      return { chainNodeIds: null, chainEdgeIds: null };
    }
    const chain = getChainIds(selectedNodeId, edges);
    return { chainNodeIds: chain.nodeIds, chainEdgeIds: chain.edgeIds };
  }, [selectedNodeId, edges]);

  // Apply highlight classes
  useEffect(() => {
    if (!chainNodeIds) {
      // Reset all to full opacity
      setNodes((nds) =>
        nds.map((n) => ({
          ...n,
          selected: false,
          style: { ...n.style, opacity: 1 },
        })),
      );
      setEdges((eds) =>
        eds.map((e) => ({
          ...e,
          selected: false,
          style: { ...e.style, opacity: undefined },
        })),
      );
      return;
    }

    setNodes((nds) =>
      nds.map((n) => ({
        ...n,
        selected: n.id === selectedNodeId,
        style: {
          ...n.style,
          opacity: chainNodeIds.has(n.id) ? 1 : 0.15,
          transition: "opacity 200ms ease",
        },
      })),
    );

    setEdges((eds) =>
      eds.map((e) => ({
        ...e,
        selected: chainEdgeIds?.has(e.id) ?? false,
        style: {
          ...e.style,
          opacity: chainEdgeIds?.has(e.id) ? 1 : 0.08,
          transition: "opacity 200ms ease",
        },
      })),
    );
  }, [chainNodeIds, chainEdgeIds, selectedNodeId, setNodes, setEdges]);

  // ── Interaction ─────────────────────────────────────────────────────────
  const onNodeClick = useCallback(
    (_: React.MouseEvent, node: Node) => {
      setSelectedNode(selectedNodeId === node.id ? null : node.id);
    },
    [selectedNodeId, setSelectedNode],
  );

  const onPaneClick = useCallback(() => {
    setSelectedNode(null);
  }, [setSelectedNode]);

  // ── Empty state ─────────────────────────────────────────────────────────
  if (!result) {
    return (
      <div className="w-full h-full flex items-center justify-center text-muted-foreground">
        <div className="text-center space-y-2">
          <div className="text-4xl opacity-20">
            <GitBranch className="w-10 h-10 mx-auto" />
          </div>
          <p className="text-sm">Provenance chain graph will appear here</p>
          <p className="text-xs text-muted-foreground">
            Run a query to trace every claim back to its source
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className="w-full h-full relative">
      <ArrowMarkers />
      <ReactFlow
        nodes={nodes}
        edges={edges}
        nodeTypes={nodeTypes}
        edgeTypes={edgeTypes}
        onNodesChange={onNodesChange}
        onEdgesChange={onEdgesChange}
        onNodeClick={onNodeClick}
        onPaneClick={onPaneClick}
        colorMode={resolvedTheme as "light" | "dark"}
        fitView
        fitViewOptions={{ padding: 0.3 }}
        minZoom={0.1}
        maxZoom={3}
        proOptions={{ hideAttribution: true }}
      >
        <Background gap={24} size={1} />
        <Controls showInteractive={false} />

        {/* Top-left: Depth control */}
        <Panel position="top-left">
          <DepthControl depth={depth} onChange={setDepth} />
        </Panel>

        {/* Bottom-left: Legend / stats */}
        <Panel position="bottom-left">
          <GraphLegend stats={graphStats} />
        </Panel>

        {/* Top-right: Selected node info */}
        {selectedNodeId && (
          <Panel position="top-right">
            <div className="bg-card/90 backdrop-blur border rounded-lg px-3 py-2 shadow-sm max-w-xs">
              <div className="flex items-center gap-1.5 mb-1">
                <ZoomIn className="w-3 h-3 text-muted-foreground" />
                <span className="text-[10px] font-mono text-muted-foreground uppercase tracking-wider">
                  Chain Focus
                </span>
              </div>
              <p className="text-xs font-mono truncate">{selectedNodeId}</p>
              <p className="text-[9px] text-muted-foreground mt-0.5">
                {chainNodeIds ? chainNodeIds.size : 0} nodes in chain |{" "}
                {chainEdgeIds ? chainEdgeIds.size : 0} edges
              </p>
              <p className="text-[8px] text-muted-foreground mt-1">
                Click empty space to deselect
              </p>
            </div>
          </Panel>
        )}

        <MiniMap
          nodeColor={(n) => {
            if (n.type === "source") return "var(--prov-source)";
            if (n.type === "vyapti") return "var(--prov-vyapti)";
            const label = (n.data as Record<string, unknown>)?.arg as
              | { label?: string }
              | undefined;
            if (label?.label === "in") return "var(--label-in)";
            if (label?.label === "out") return "var(--label-out)";
            return "var(--label-undecided)";
          }}
          className="!bottom-2 !right-2"
          pannable
          zoomable
        />
      </ReactFlow>
    </div>
  );
}
