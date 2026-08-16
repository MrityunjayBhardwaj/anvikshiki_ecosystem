"use client";

import { useEffect, useCallback } from "react";
import {
  ReactFlow,
  Background,
  Controls,
  MiniMap,
  useNodesState,
  useEdgesState,
  type Node,
  type Edge,
  type NodeTypes,
  type EdgeTypes,
} from "@xyflow/react";
import "@xyflow/react/dist/style.css";
import { useTheme } from "next-themes";
import { useQueryStore } from "@/store/queryStore";
import { ArgumentNode as ArgNodeComponent } from "./ArgumentNode";
import { AttackEdge as AttackEdgeComponent } from "./AttackEdge";
import { applyDagreLayout } from "./graphLayout";
import type { EngineResult, ArgumentNode as ArgNodeType } from "@/lib/types";

const nodeTypes: NodeTypes = {
  argument: ArgNodeComponent,
};

const edgeTypes: EdgeTypes = {
  attack: AttackEdgeComponent,
};

function transformToNodes(result: EngineResult): Node[] {
  const args = Object.values(result.arguments) as ArgNodeType[];
  return args.map((arg) => ({
    id: arg.id,
    type: "argument",
    position: { x: 0, y: 0 }, // layout applied after
    data: { arg, label: arg.label },
  }));
}

function transformToEdges(result: EngineResult): Edge[] {
  return result.attacks.map((attack) => ({
    id: attack.id,
    source: attack.attacker,
    target: attack.target,
    type: "attack",
    data: { attack },
    animated: attack.attack_type === "rebutting",
  }));
}

export function ArgumentationGraph() {
  const { result, selectedNodeId, setSelectedNode } = useQueryStore();
  const { resolvedTheme } = useTheme();

  const [nodes, setNodes, onNodesChange] = useNodesState<Node>([]);
  const [edges, setEdges, onEdgesChange] = useEdgesState<Edge>([]);

  useEffect(() => {
    if (!result) {
      setNodes([]);
      setEdges([]);
      return;
    }
    const rawNodes = transformToNodes(result);
    const rawEdges = transformToEdges(result);
    const laid = applyDagreLayout(rawNodes, rawEdges);
    setNodes(laid);
    setEdges(rawEdges);
  }, [result, setNodes, setEdges]);

  // Highlight selected node
  useEffect(() => {
    setNodes((nds) =>
      nds.map((n) => ({
        ...n,
        selected: n.id === selectedNodeId,
      }))
    );
  }, [selectedNodeId, setNodes]);

  const onNodeClick = useCallback(
    (_: React.MouseEvent, node: Node) => {
      setSelectedNode(selectedNodeId === node.id ? null : node.id);
    },
    [selectedNodeId, setSelectedNode]
  );

  if (!result) {
    return (
      <div className="w-full h-full flex items-center justify-center text-muted-foreground">
        <div className="text-center space-y-2">
          <div className="text-4xl opacity-20">⬡</div>
          <p className="text-sm">Argumentation graph will appear here</p>
          <p className="text-xs text-muted-foreground">
            Run a query to build the ASPIC+ argument structure
          </p>
        </div>
      </div>
    );
  }

  return (
    <ReactFlow
      nodes={nodes}
      edges={edges}
      nodeTypes={nodeTypes}
      edgeTypes={edgeTypes}
      onNodesChange={onNodesChange}
      onEdgesChange={onEdgesChange}
      onNodeClick={onNodeClick}
      colorMode={resolvedTheme as "light" | "dark"}
      fitView
      fitViewOptions={{ padding: 0.2 }}
      minZoom={0.3}
      maxZoom={2}
    >
      <Background gap={20} size={1} />
      <Controls showInteractive={false} />
      <MiniMap
        nodeColor={(n) => {
          const label = (n.data as Record<string, unknown>)?.label as string;
          if (label === "in") return "var(--label-in)";
          if (label === "out") return "var(--label-out)";
          return "var(--label-undecided)";
        }}
        className="!bottom-2 !right-2"
      />
    </ReactFlow>
  );
}
