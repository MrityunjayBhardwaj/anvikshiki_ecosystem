# Ānvīkṣikī Webapp — Design Document

> Branch: `webapp` · Author: Session 13 · Date: 2026-03-09
> **Updated:** 2026-03-09 — aligned to shadcn/ui CLI v4, Next.js 15 + React 19, React Flow v12 (`@xyflow/react`), FastAPI native SSE

---

## Table of Contents

1. [Goals & Non-Goals](#1-goals--non-goals)
2. [Stack Decision](#2-stack-decision)
3. [Architecture Overview](#3-architecture-overview)
4. [Backend API Design](#4-backend-api-design)
5. [Frontend Structure](#5-frontend-structure)
6. [Screen-by-Screen Design](#6-screen-by-screen-design)
   - 6.1 [Landing / KB Select](#61-landing--kb-select)
   - 6.2 [Query Studio (main screen)](#62-query-studio-main-screen)
   - 6.3 [Argumentation Graph](#63-argumentation-graph-panel)
   - 6.4 [Pipeline Trace Drawer](#64-pipeline-trace-drawer)
   - 6.5 [KB Inspector Sheet](#65-kb-inspector-sheet)
   - 6.6 [History & Sessions](#66-history--sessions)
7. [Component Library (shadcn/ui)](#7-component-library-shadcnui)
8. [Data Flows](#8-data-flows)
9. [Visual Language & Design Tokens](#9-visual-language--design-tokens)
10. [File & Directory Layout](#10-file--directory-layout)
11. [API ↔ UI Type Contracts](#11-api--ui-type-contracts)
12. [Streaming & Real-time UX](#12-streaming--real-time-ux)
13. [Implementation Phases](#13-implementation-phases)

---

## 1. Goals & Non-Goals

### Goals

- **Expose the full engine output visually.** The argumentation framework, epistemic labels (IN/OUT/UNDECIDED), provenance tags, hetvābhāsa violations, and coverage routing are invisible when using the Python API. The webapp makes every layer of the pipeline inspectable.
- **Make it feel like a professional reasoning tool, not a chatbot.** The output is not a chat bubble. It is a structured epistemic report with a reasoning trace.
- **Zero configuration to run.** `pnpm dev` (frontend) + `uvicorn` (backend) should be the entire setup. No databases, no auth in v1.
- **Support loading any YAML knowledge base + guide directory.** The UI is KB-agnostic. The business expert domain is the demo KB.

### Non-Goals

- Auth, multi-user, persistence across restarts (v1)
- Mobile-first (desktop-optimized, responsive is fine)
- Guide generation UI (that is a separate product surface)
- DSPy optimizer UI (deferred to v2)

---

## 2. Stack Decision

| Layer | Choice | Version | Rationale |
|-------|--------|---------|-----------|
| Frontend framework | **Next.js** (App Router) | **15** | RSC for static panels, client components for live query state; full React 19 support |
| UI components | **shadcn/ui** + Tailwind CSS | **CLI v4** | Copy-owned components, OKLCH color system, dark mode first, accessible |
| Graph visualization | **React Flow** | **v12** (`@xyflow/react`) | Custom nodes/edges, SSR support, built-in dark mode, TypeScript-first |
| State management | **Zustand** | latest | Lightweight; one store per concern (query, kb, trace) |
| Backend | **FastAPI** | **0.135+** | Native SSE support; same process as engine |
| Streaming | **Server-Sent Events (SSE)** | FastAPI built-in | Each pipeline stage emits a progress event; `EventSourceResponse` + `ServerSentEvent` |
| Python↔JS types | **Pydantic → JSON Schema → zod** | — | Auto-generated type safety across the boundary |
| Package manager | **pnpm** | — | Workspace-friendly, fast |
| Icons | **Lucide React** (bundled with shadcn) | — | Consistent with shadcn design language |

### Key version notes

**shadcn/ui CLI v4 (March 2026):**
- CLI package renamed: use `pnpm dlx shadcn@latest` (not `shadcn-ui`)
- Default style is now **`new-york`** (old default style deprecated)
- Colors moved from HSL → **OKLCH** by default (perceptually uniform, better on modern displays)
- New components: `chart` (Recharts composition), `data-table` (TanStack Table), `sidebar` (responsive collapsible)
- `components.json` `$schema` → `https://ui.shadcn.com/schema.json`

**React Flow v12 — breaking changes from v11:**

| v11 | v12 |
|-----|-----|
| `import ReactFlow from 'reactflow'` | `import { ReactFlow } from '@xyflow/react'` |
| `import 'reactflow/dist/style.css'` | `import '@xyflow/react/dist/style.css'` |
| `node.width` / `node.height` | `node.measured.width` / `node.measured.height` |
| `xPos` / `yPos` in node | `positionAbsoluteX` / `positionAbsoluteY` |
| `parentNode` | `parentId` |
| `nodeInternals` | `nodeLookup` |
| `onEdgeUpdate` | `onReconnect` |
| `updateEdge()` | `reconnectEdge()` |
| `getTransformForBounds()` | removed |

New in v12: SSR/SSG support, built-in `ColorMode` for dark mode, computing flows API.

**FastAPI native SSE (v0.135+):**
- No longer need `sse-starlette` package — FastAPI ships `EventSourceResponse` and `ServerSentEvent` natively
- Auto keep-alive pings every 15s, `Cache-Control: no-cache`, `X-Accel-Buffering: no` headers set automatically
- Usage: `async def route() -> AsyncIterable[ServerSentEvent]: yield ServerSentEvent(data={...}, event="stage:grounding")`

**Why not WebSockets?** SSE is one-directional (server → client) and sufficient here. The only real-time direction is pipeline progress → browser. Queries go over HTTP POST. SSE avoids the reconnect complexity of WS for this use case.

**Why React Flow instead of D3?** The argumentation graph is a node-edge graph with structured data per node. React Flow v12 gives us customizable React components per node (EpistemicStatus badge, ProvenanceTag tooltip, belief bar) without writing canvas rendering code, plus first-class SSR and dark mode out of the box.

---

## 3. Architecture Overview

```
┌──────────────────────────────────────────────────────┐
│                   Browser (Next.js)                  │
│                                                      │
│  Landing → KB Select                                 │
│  Query Studio ← main screen                         │
│    ├── Query Input (Command)                         │
│    ├── Argumentation Graph (React Flow)             │
│    ├── Response Panel (Card)                        │
│    ├── Provenance Table (DataTable)                 │
│    └── Pipeline Trace (Drawer)                      │
│  KB Inspector (Sheet)                               │
│  History (Dialog)                                   │
└────────────┬─────────────────────────────────────────┘
             │  HTTP / SSE
             ▼
┌──────────────────────────────────────────────────────┐
│              FastAPI Backend (Python)                │
│                                                      │
│  POST /api/query          → full engine result       │
│  GET  /api/query/stream   → SSE pipeline stages      │
│  GET  /api/kb/list        → available KBs            │
│  POST /api/kb/load        → load KB + compile        │
│  GET  /api/kb/inspect     → vyaptis, hetvabhasas     │
│  GET  /api/health         → readiness check          │
└────────────┬─────────────────────────────────────────┘
             │  Python function call
             ▼
┌──────────────────────────────────────────────────────┐
│        Ānvīkṣikī Engine (anvikshiki_v4)             │
│                                                      │
│  initialize_engine(kb_yaml, guide_dir)               │
│  engine.forward_with_coverage(query)                 │
│    → dspy.Prediction (response, provenance,          │
│                        violations, uncertainty,       │
│                        coverage, augmentation)        │
└──────────────────────────────────────────────────────┘
```

The engine runs in the same FastAPI process. `initialize_engine()` is called once on startup (or on KB switch) — compile-time work happens then. Queries are cheap once compiled.

---

## 4. Backend API Design

### `POST /api/kb/load`

```typescript
// Request
{ kb_yaml: string, guide_dir: string, grounding_mode?: "minimal" | "partial" | "full" }

// Response
{
  kb_id: string,           // hash of kb_yaml path
  domain: string,          // ks.domain
  vyapti_count: number,
  hetvabhasa_count: number,
  guide_chapter_count: number,
  synonym_table_size: number,
  compile_time_ms: number,
  status: "ready"
}
```

### `POST /api/query`

```typescript
// Request
{ query: string, mode?: GroundingMode, interpreted_intent?: string }

// Response: EngineResult (see §11)
```

### `GET /api/query/stream?query=...&mode=...`

Server-Sent Events. Each event has a `type` and `data`:

| Event type | When emitted | Data |
|-----------|-------------|------|
| `stage:grounding` | After grounding completes | `{ predicates, confidence, disputed, mode }` |
| `stage:coverage` | After coverage check | `{ decision, coverage_ratio, matched, unmatched }` |
| `stage:augmentation` | After T3b (if DECLINE) | `{ augmented, new_vyapti_count, reason }` |
| `stage:compilation` | After compile_t2 | `{ argument_count, attack_count }` |
| `stage:extension` | After grounded semantics | `{ in_count, out_count, undecided_count }` |
| `stage:synthesis` | After LLM synthesis | `{ response, sources_cited }` |
| `complete` | Final result | Full `EngineResult` |
| `error` | Any exception | `{ message, stage }` |

This powers the live Pipeline Trace panel — each stage lights up as it completes.

### `GET /api/kb/inspect`

```typescript
{
  domain: string,
  description: string,
  vyaptis: VyaptiSummary[],     // id, head, body, epistemic_status, sources
  hetvabhasas: HetvabhasaSummary[],
  fine_grained_vyaptis: FineGrainedVyaptiSummary[],
}
```

---

## 5. Frontend Structure

```
webapp/
├── app/
│   ├── layout.tsx              # Root layout: ThemeProvider, Toaster, KBProvider
│   ├── page.tsx                # Landing / KB select
│   ├── studio/
│   │   └── page.tsx            # Query Studio (main screen)
│   └── api/                    # Next.js route handlers (proxy to FastAPI or direct)
├── components/
│   ├── ui/                     # shadcn auto-generated components (never edited directly)
│   ├── kb/
│   │   ├── KBSelectCard.tsx
│   │   ├── KBInspectorSheet.tsx
│   │   ├── VyaptiRow.tsx
│   │   └── HetvabhasaBadge.tsx
│   ├── query/
│   │   ├── QueryInput.tsx
│   │   ├── GroundingModeToggle.tsx
│   │   └── QueryHistory.tsx
│   ├── result/
│   │   ├── ResponseCard.tsx
│   │   ├── EpistemicStatusBadge.tsx
│   │   ├── ProvenanceTable.tsx
│   │   ├── ViolationsPanel.tsx
│   │   └── CoverageIndicator.tsx
│   ├── graph/
│   │   ├── ArgumentationGraph.tsx   # React Flow wrapper
│   │   ├── ArgumentNode.tsx         # Custom node: label, belief bar, pramana
│   │   ├── AttackEdge.tsx           # Custom edge: hetvabhasa type, animated for active
│   │   └── graphLayout.ts           # dagre layout algorithm
│   ├── trace/
│   │   ├── PipelineTraceDrawer.tsx
│   │   ├── StageCard.tsx
│   │   └── GroundingStageDetail.tsx
│   └── layout/
│       ├── TopNav.tsx
│       ├── StatusBar.tsx
│       └── ThemeToggle.tsx
├── lib/
│   ├── api.ts                  # Typed fetch wrappers for all backend routes
│   ├── sse.ts                  # SSE client hook (useQueryStream)
│   ├── graphTransform.ts       # EngineResult → React Flow nodes/edges
│   └── types.ts                # Zod schemas + inferred TypeScript types
├── store/
│   ├── kbStore.ts              # Zustand: loaded KB, compile artifacts
│   ├── queryStore.ts           # Zustand: current query, result, loading state
│   └── traceStore.ts           # Zustand: SSE stage events (live trace)
└── styles/
    └── globals.css             # Tailwind + CSS custom properties for design tokens
```

---

## 6. Screen-by-Screen Design

### 6.1 Landing / KB Select

**Purpose:** Select or upload a knowledge base. The first screen a new user sees.

**Layout:** Full-width centered column. Header with project name + tagline. Below: a grid of KB cards (one per available YAML in `data/`). CTA to load a custom YAML via file picker.

```
┌──────────────────────────────────────────────────────────────┐
│  Ānvīkṣikī                                   ◐ Dark  [Docs] │
├──────────────────────────────────────────────────────────────┤
│                                                              │
│   Neurosymbolic Reasoning over Structured Knowledge          │
│   Query your knowledge base with formal epistemic rigor.     │
│                                                              │
│  ┌────────────────────────┐   ┌───────────────────────┐     │
│  │ 📚 Business Expert     │   │ ➕ Load Custom KB      │     │
│  │                        │   │                       │     │
│  │ 11 vyāptis             │   │ Drop YAML here or     │     │
│  │ 8 hetvābhāsas          │   │ browse filesystem     │     │
│  │ 12 guide chapters      │   │                       │     │
│  │                        │   │                       │     │
│  │ [Open Studio →]        │   │ [Browse files]        │     │
│  └────────────────────────┘   └───────────────────────┘     │
│                                                              │
└──────────────────────────────────────────────────────────────┘
```

**shadcn components:**
- `Card`, `CardHeader`, `CardContent`, `CardFooter` for each KB
- `Button` (variant="default") for "Open Studio"
- `Input` (type="file") + drag zone for custom KB
- `Badge` for vyapti/hetvabhasa counts
- `Skeleton` while compile artifacts load

**State transition:** Clicking "Open Studio" calls `POST /api/kb/load`, shows a compile progress toast, then navigates to `/studio`.

---

### 6.2 Query Studio (Main Screen)

This is the primary working surface. Three-column layout on desktop:

```
┌──────────┬──────────────────────────────────┬───────────────┐
│  LEFT    │           CENTER                 │     RIGHT     │
│  panel   │         (main area)              │   (details)   │
│  240px   │           flex-1                 │   320px       │
├──────────┼──────────────────────────────────┼───────────────┤
│          │  ┌──────────────────────────────┐│               │
│ KB       │  │  Query Input                 ││  Response     │
│ Summary  │  │  ─────────────────────────── ││  ─────────── │
│          │  │  [ How do unit economics...] ││  "Unit eco-   │
│ Vyāptis  │  │  [MINIMAL][PARTIAL][FULL]   ││  nomics are   │
│ ───────  │  │  [Run Query →]               ││  ESTABLISHED  │
│ V01 ...  │  └──────────────────────────────┘│  via V01 +    │
│ V02 ...  │                                  │  V03..."      │
│ V03 ...  │  ┌──────────────────────────────┐│               │
│ ...      │  │  Argumentation Graph         ││  Provenance   │
│          │  │                              ││  ─────────── │
│ Hetvā-   │  │  [React Flow canvas]         ││  V01 PRATYAK │
│ bhāsas   │  │                              ││  V03 ANUMANA │
│ ───────  │  │                              ││               │
│ H01 ...  │  │                              ││  Violations   │
│ H02 ...  │  │                              ││  ─────────── │
│          │  └──────────────────────────────┘│  ⚠ savyabhi- │
│ [Inspect │                                  │  cara on A05  │
│  KB ↗]   │  [Pipeline Trace ↗]              │               │
└──────────┴──────────────────────────────────┴───────────────┘
```

#### Left Panel — KB Summary

Thin sidebar: domain name, compile stats (vyapti count, hetvabhasa count, coverage mode). Below: scrollable list of `VyaptiRow` components (id + head predicate). Below: `HetvabhasaBadge` list. Footer: "Inspect Full KB" button that opens the KB Inspector Sheet.

**shadcn:** `ScrollArea`, `Separator`, `Badge`, `Button` (variant="ghost"), `Tooltip` (hover a vyapti → show its body, sources, epistemic status).

#### Center — Query Input

Full-width `Command`-style input that supports:
- Free-form natural language query
- `Tab` to autocomplete from recent queries
- Grounding mode toggle (segmented control: MINIMAL / PARTIAL / FULL)
- Query submit (Enter or button)

Below the input: the Argumentation Graph takes all remaining vertical space.

#### Right Panel — Result Details

Tabs: **Response** | **Provenance** | **Violations** | **Coverage**

**Response tab:**
- `ResponseCard`: the synthesized LLM answer
- Below the answer: `EpistemicStatusBadge` grid — one badge per conclusion (ESTABLISHED green / HYPOTHESIS amber / CONTESTED orange / OPEN gray)
- Sources cited: `Badge` list with source IDs

**Provenance tab:**
- `ProvenanceTable`: each accepted conclusion as a row
  - Columns: Predicate, Pramāṇa (icon+label), Belief (mini progress bar), Uncertainty, Depth, Sources
  - Row expandable: shows tag ⊗ arithmetic for chained inferences

**Violations tab:**
- `ViolationsPanel`: hetvābhāsa violations as warning cards
  - Each card: attacker argument ID, target conclusion, hetvābhāsa type (badge), attack type (rebuttal/undercutting/undermining)
  - Empty state: green checkmark + "No formal fallacies detected"

**Coverage tab:**
- `CoverageIndicator`: ring chart showing matched / unmatched / augmented predicates
- Decision badge: FULL (green) / PARTIAL (amber) / DECLINE→AUGMENTED (blue) / DECLINE→OUT-OF-DOMAIN (red)
- Matched predicates table: predicate name + match type (exact / synonym / token)

---

### 6.3 Argumentation Graph Panel

The argumentation graph is the most distinctive visual element. It makes the ASPIC+ reasoning visible.

**Nodes — two types:**

*Argument node* (each Argument in the framework):

```
┌─────────────────────────────┐
│  A0003                      │  ← argument ID
│  value_creation             │  ← conclusion predicate
│  ────────────────────────── │
│  ████████░░  0.808          │  ← belief bar (ProvenanceTag.belief)
│  ANUMANA  •  IN             │  ← pramana badge + Label badge
│  V01 → V03                  │  ← rule chain (tooltip: full rule body)
└─────────────────────────────┘
```

Color coding:
- Border: **green** if Label=IN, **red** if Label=OUT, **gray** if Label=UNDECIDED
- Background: tinted version of the border color at 10% opacity
- Header accent strip: EpistemicStatus color (ESTABLISHED=emerald, HYPOTHESIS=amber, CONTESTED=orange, OPEN=slate)

*Premise node* (facts from the grounded query):

```
┌────────────────────────┐
│  ◈ FACT                │
│  positive_unit_econom- │
│  ics                   │
│  ──────────────────    │
│  PRATYAKSA  b=0.85     │
└────────────────────────┘
```

Octagon shape. Always Label=IN (premises are accepted). Filled blue-gray.

**Edges — three attack types:**

| Type | Visual |
|------|--------|
| Rebuttal (contradicts conclusion) | Solid red arrow, label: "rebuts" |
| Undercutting (attacks rule application) | Dashed red arrow, label: hetvābhāsa type |
| Undermining (attacks premise) | Dotted red arrow, label: "undermines" |

Support edges (argument uses another as premise): soft gray arrows, thin, no label. Only shown if user toggles "Show support edges."

**Layout:**
- **dagre** top-to-bottom layout. Premises at bottom. Final conclusions at top.
- Grouping: DECLINED arguments (Label=OUT) rendered as a cluster in the bottom-right corner, visually separated.
- Pan + zoom + fit-to-view on result load.
- Click any node → right panel highlights that argument's row in the Provenance table. Right panel scrolls to it.
- Hover any edge → tooltip shows full `Attack` object: `Attack(attacker=A0005, target=A0003, type="undercutting", hetvabhasa="savyabhicara", specificity_weight=0.73)`

**Controls:**
- Floating toolbar (top-right of graph): Fit View, Zoom In, Zoom Out, Toggle Support Edges, Export PNG
- Legend (collapsible, bottom-left): IN / OUT / UNDECIDED / Premise, + edge types

**React Flow v12 implementation notes:**

```typescript
// components/graph/ArgumentationGraph.tsx
// IMPORTANT: React Flow v12 package is @xyflow/react (not reactflow)
import { ReactFlow, Background, Controls, useNodesState,
         useEdgesState, ColorMode } from '@xyflow/react'
import '@xyflow/react/dist/style.css'   // ← path changed in v12
import { ArgumentNode } from './ArgumentNode'
import { AttackEdge } from './AttackEdge'
import { useTheme } from 'next-themes'

const nodeTypes = { argument: ArgumentNode, premise: ArgumentNode }
const edgeTypes = { attack: AttackEdge }

export function ArgumentationGraph({ result }: { result: EngineResult }) {
  const { resolvedTheme } = useTheme()
  const [nodes, , onNodesChange] = useNodesState(transformToNodes(result))
  const [edges, , onEdgesChange] = useEdgesState(transformToEdges(result))

  return (
    <ReactFlow
      nodes={nodes} edges={edges}
      nodeTypes={nodeTypes} edgeTypes={edgeTypes}
      onNodesChange={onNodesChange} onEdgesChange={onEdgesChange}
      colorMode={resolvedTheme as ColorMode}  // ← v12 built-in dark mode
      fitView
    >
      <Background /> <Controls />
    </ReactFlow>
  )
}

// components/graph/graphLayout.ts
// Node dimensions in v12: use node.measured.width / node.measured.height
// (not node.width / node.height — those are input dimensions, not computed)
import dagre from '@dagrejs/dagre'

export function applyDagreLayout(nodes: Node[], edges: Edge[]) {
  const g = new dagre.graphlib.Graph()
  g.setGraph({ rankdir: 'BT', ranksep: 80, nodesep: 40 })
  g.setDefaultEdgeLabel(() => ({}))

  nodes.forEach(n => g.setNode(n.id, {
    width: n.measured?.width ?? 200,   // ← v12: use measured dimensions
    height: n.measured?.height ?? 80,
  }))
  edges.forEach(e => g.setEdge(e.source, e.target))
  dagre.layout(g)

  return nodes.map(n => {
    const pos = g.node(n.id)
    return { ...n, position: { x: pos.x - (n.measured?.width ?? 200) / 2,
                                y: pos.y - (n.measured?.height ?? 80) / 2 } }
  })
}
```

---

### 6.4 Pipeline Trace Drawer

Opened by clicking "Pipeline Trace ↗" in the footer of the center column. A `Sheet` that slides in from the right (full height, 480px wide).

The trace shows every stage in order, live-updating via SSE during query execution.

```
Pipeline Trace                                    [×]
─────────────────────────────────────────────────────
  1  GROUNDING                         ✓  42ms
     Mode: PARTIAL (N=3 ensemble)
     Predicates: unit_economics, positive_margin, ...
     Confidence: 0.91
     Disputed: none
     ▼ [Show raw calls]

  2  COVERAGE                          ✓  3ms
     Decision: FULL (ratio: 0.82)
     Matched: 4/5 predicates (exact × 3, synonym × 1)
     Unmatched: market_position (→ declined)

  3  COMPILATION                       ✓  8ms
     Arguments: 14
     Attacks: 6
     Strict rules: 3 / Defeasible rules: 11

  4  EXTENSION                         ✓  12ms
     IN: 9    OUT: 3    UNDECIDED: 2
     Grounded semantics (vāda)
     ▼ [Show label table]

  5  SYNTHESIS                         ✓  1,203ms
     LLM: claude-sonnet-4-6
     Response tokens: 312
     Sources cited: 4

─────────────────────────────────────────────────────
Total: 1,268ms    [Copy as JSON]    [Download trace]
```

During live query: each stage row starts as a `Skeleton`, transitions to a spinner (●○○), then resolves to ✓ with timing. The SSE `stage:*` events drive this.

Each stage is a `StageCard` (`Accordion` item) that expands to show raw data.

**shadcn:** `Sheet`, `SheetContent`, `SheetHeader`, `Accordion`, `AccordionItem`, `AccordionTrigger`, `AccordionContent`, `Badge`, `Skeleton`, `Progress`, `Button`.

---

### 6.5 KB Inspector Sheet

Opened from the left panel "Inspect KB" button. Full-height `Sheet` from the left side. 560px wide.

**Tabs:** Vyāptis | Hetvābhāsas | Fine-Grained | Schema

**Vyāptis tab:**

Each vyapti as a `Card`:
```
┌─────────────────────────────────────────────────────┐
│  V01  positive_unit_economics                       │
│  ─────────────────────────────────────────────────  │
│  IF  positive_margin AND cost_structure_efficient   │
│  THEN  unit_economics_positive                      │
│                                                     │
│  ● DEFEASIBLE          ESTABLISHED                  │
│  Sources: McKinsey 2024 (PRATYAKSA), Thales p.47   │
│                                                     │
│  ProvenanceTag: b=0.90 · d=0.05 · u=0.05           │
│  Decay: 0.92  Trust: 0.88  Depth: 1                │
└─────────────────────────────────────────────────────┘
```

Clicking a vyapti highlights the corresponding node(s) in the argumentation graph (if a query result is loaded).

**Hetvābhāsas tab:**

Each hetvabhasa as a `Card` with its pattern, example, and which vyaptis it guards.

```
┌─────────────────────────────────────────────────────┐
│  H01  Savyabhicāra (Too-Wide Middle Term)           │
│  ─────────────────────────────────────────────────  │
│  Pattern: rule applies across conflicting contexts  │
│  Guards: V03, V07, V11                              │
│  Attack type: undercutting                          │
│                                                     │
│  Example: "profitable" without controlling for      │
│  market phase (growth vs. mature)                   │
└─────────────────────────────────────────────────────┘
```

**Schema tab:** JSON view of the raw `KnowledgeStore` Pydantic model. `ScrollArea` + syntax highlighting (`shiki` or just `<pre>`).

---

### 6.6 History & Sessions

Accessible from the top nav (clock icon). A `Dialog` showing all queries from the current session.

Table columns: Query text (truncated), Mode, Coverage decision, Extension IN count, Time.

Clicking a row restores that query's full result — graph, provenance, violations. The engine does NOT re-run; the stored `EngineResult` is replayed into the store.

**shadcn:** `Dialog`, `DialogContent`, `Table`, `TableHeader`, `TableRow`, `TableCell`, `Badge`.

---

## 7. Component Library (shadcn/ui)

**Init (run once):**

```bash
pnpm dlx shadcn@latest init
# Prompts: style → new-york, base color → neutral, CSS variables → yes
```

**Add all components:**

```bash
pnpm dlx shadcn@latest add \
  button badge card separator sheet drawer \
  command input textarea label \
  tabs accordion scroll-area \
  dialog tooltip popover \
  progress skeleton \
  table \
  select toggle-group \
  toast sonner \
  hover-card \
  collapsible \
  chart \
  sidebar
```

**`components.json` (generated by init — do not edit manually):**

```json
{
  "$schema": "https://ui.shadcn.com/schema.json",
  "style": "new-york",
  "rsc": true,
  "tsx": true,
  "tailwind": {
    "config": "tailwind.config.ts",
    "css": "app/globals.css",
    "baseColor": "neutral",
    "cssVariables": true
  },
  "aliases": {
    "components": "@/components",
    "utils": "@/lib/utils"
  }
}
```

Custom components built on top (not from shadcn, but use shadcn primitives):

| Component | Built from | Purpose |
|-----------|------------|---------|
| `EpistemicStatusBadge` | `Badge` | Color-coded by status enum |
| `PramanaIcon` | Lucide icons | Icon per PramanaType (eye=PRATYAKSA, brain=ANUMANA, book=SABDA, scale=UPAMANA) |
| `BeliefBar` | `Progress` | Narrow belief [0,1] bar with uncertainty overlay |
| `ProvTagTooltip` | `HoverCard` | Hover → show full (b,d,u) triple + arithmetic |
| `ArgumentNode` | Custom div | React Flow node, uses Badge, BeliefBar, PramanaIcon |
| `AttackEdge` | React Flow `EdgeProps` | Custom edge with label, color, dash pattern |
| `StageCard` | `AccordionItem` + `Skeleton` | Live-updating pipeline stage |
| `CoverageRing` | SVG circle | Donut chart: matched/unmatched ratio |
| `GroundingModeToggle` | `ToggleGroup` | MINIMAL/PARTIAL/FULL selector |

---

## 8. Data Flows

### Query execution flow (full)

```
User types query
  → QueryInput.tsx: local state
  → User presses Enter
  → queryStore.setLoading(true)
  → api.ts: POST /api/query { query, mode }
     (parallel) sse.ts: GET /api/query/stream
       → stage:grounding → traceStore.addStage(grounding)
       → stage:coverage  → traceStore.addStage(coverage)
       → stage:compilation → traceStore.addStage(compilation)
       → stage:extension → traceStore.addStage(extension)
       → stage:synthesis → traceStore.addStage(synthesis)
       → complete → queryStore.setResult(EngineResult)
  → graphTransform.ts: EngineResult → { nodes[], edges[] }
  → ArgumentationGraph re-renders with new graph
  → ResponseCard shows response
  → ProvenanceTable shows provenance
  → ViolationsPanel shows violations
  → CoverageIndicator shows coverage
  → queryStore.setLoading(false)
```

### KB load flow

```
User clicks KB card (or drops YAML)
  → kbStore.setLoading(true)
  → api.ts: POST /api/kb/load { kb_yaml, guide_dir }
  → toast: "Compiling knowledge base..."
  → Response: { kb_id, domain, vyapti_count, ... }
  → kbStore.setKB(kb)
  → toast: "Ready — 11 vyāptis compiled in 1.2s"
  → navigate to /studio
```

### Graph click → right panel sync

```
User clicks ArgumentNode (A0003)
  → graphStore.setSelectedNode("A0003")
  → ProvenanceTable watches selectedNode
  → scrolls to A0003 row
  → highlights row with ring focus
  → ProvTagTooltip auto-opens for that row
```

---

## 9. Visual Language & Design Tokens

### Color Palette (CSS custom properties)

shadcn/ui CLI v4 generates OKLCH tokens automatically in `app/globals.css` — this is now the default color format (replacing HSL). We extend the generated file with domain-specific tokens:

```css
/* app/globals.css
   Top section: shadcn-generated base tokens (do not edit)
   Bottom section: Ānvīkṣikī domain extensions */

@layer base {
  :root {
    /* ── shadcn base tokens (generated by `pnpm dlx shadcn@latest init`) ── */
    --background:          oklch(1 0 0);
    --foreground:          oklch(0.207 0.013 254.3);
    --primary:             oklch(0.205 0.105 263.9);
    --primary-foreground:  oklch(1 0 0);
    --destructive:         oklch(0.577 0.245 27.325);
    --muted:               oklch(0.961 0.006 264.5);
    --muted-foreground:    oklch(0.55 0.013 254.3);
    --border:              oklch(0.928 0.006 264.5);
    --radius:              0.5rem;
    /* ... (full list generated — do not copy-paste, let shadcn write it) */

    /* ── Ānvīkṣikī domain tokens ── */

    /* Epistemic status */
    --established:  oklch(0.72 0.17 145);    /* emerald */
    --hypothesis:   oklch(0.75 0.15 80);     /* amber */
    --provisional:  oklch(0.70 0.10 260);    /* slate-blue */
    --open:         oklch(0.60 0.00 0);      /* neutral */
    --contested:    oklch(0.70 0.18 35);     /* orange */

    /* Argumentation labels */
    --label-in:         oklch(0.72 0.17 145);  /* green */
    --label-out:        oklch(0.65 0.22 25);   /* red */
    --label-undecided:  oklch(0.65 0.00 0);    /* gray */

    /* Pramāṇa hierarchy (weakest → strongest) */
    --pramana-upamana:   oklch(0.75 0.10 300); /* violet */
    --pramana-sabda:     oklch(0.75 0.12 240); /* blue */
    --pramana-anumana:   oklch(0.70 0.15 200); /* cyan */
    --pramana-pratyaksa: oklch(0.72 0.17 145); /* emerald */

    /* Attack edge types */
    --attack-rebuttal:     oklch(0.65 0.22 25);  /* red */
    --attack-undercutting: oklch(0.70 0.18 35);  /* orange */
    --attack-undermining:  oklch(0.65 0.18 60);  /* yellow */

    /* Coverage routing */
    --coverage-full:    var(--established);
    --coverage-partial: var(--hypothesis);
    --coverage-decline: oklch(0.65 0.15 270);    /* indigo */
    --coverage-ood:     var(--label-out);
  }

  .dark {
    /* ── shadcn dark tokens (generated) ── */
    --background: oklch(0.145 0 0);
    --foreground: oklch(0.985 0 0);
    /* ... */

    /* Domain tokens: OKLCH values are perceptually stable across
       light and dark — no override needed for most tokens.
       Exception: increase chroma slightly for dark mode vibrancy */
    --established:  oklch(0.78 0.19 145);
    --hypothesis:   oklch(0.80 0.17 80);
    --contested:    oklch(0.76 0.20 35);
    --label-in:     oklch(0.78 0.19 145);
    --label-out:    oklch(0.70 0.24 25);
  }
}
```

> **Why OKLCH?** Perceptually uniform — equal numeric distance = equal perceived difference. Gradients don't pass through gray. Works with wide-gamut displays (P3). This is why shadcn switched from HSL in CLI v4.

### Typography

- Font: **Inter** (body) + **JetBrains Mono** (code, IDs, predicates, mathematical notation)
- The predicate names (`unit_economics`, `positive_margin`) always render in `font-mono`
- The Subjective Logic triples `(b=0.808, d=0.048, u=0.193)` render in `font-mono text-xs`
- Sanskrit terms (Nyāya, pramāṇa, hetvābhāsa, etc.) render in the base font but with a subtle hover tooltip explaining the term

### Spacing and Density

Professional tool ≠ marketing site. Use **compact density** by default:
- `p-3` for panels, not `p-6`
- `text-sm` for almost everything in the result panels
- `text-xs` for metadata (source IDs, timestamps, depths)
- Only the response text uses `text-base`

### Dark Mode

shadcn's default dark mode is the **primary mode**. Light mode is supported but secondary. The argumentation graph is especially suited to dark backgrounds — node glow effects work better on dark.

Node glow: `box-shadow: 0 0 12px var(--label-in)` for IN nodes (green glow), etc. Applied as a CSS class on the React Flow node wrapper.

---

## 10. File & Directory Layout

The webapp lives alongside the existing Python engine in the monorepo:

```
anvikshiki_ecosystem/
├── anvikshiki_v4/         # Python engine (unchanged)
├── webapp/                # New — Next.js app
│   ├── app/
│   │   ├── layout.tsx
│   │   ├── page.tsx
│   │   └── studio/page.tsx
│   ├── components/        # (see §5)
│   ├── lib/
│   ├── store/
│   ├── styles/
│   ├── public/
│   │   └── favicon.svg    # Ānvīkṣikī logo (devanagari आ stylized)
│   ├── package.json
│   ├── tsconfig.json
│   ├── tailwind.config.ts
│   ├── next.config.ts
│   └── components.json    # shadcn config
├── backend/               # New — FastAPI server
│   ├── main.py            # FastAPI app, routes, SSE
│   ├── engine_state.py    # Singleton: loaded KB + engine instance
│   ├── models.py          # Pydantic request/response models
│   └── sse_pipeline.py    # SSE event generator (wraps engine stages)
├── scripts/               # existing
├── docs/
│   └── webapp_design.md   # this file
└── pyproject.toml         # add fastapi>=0.135, uvicorn (no sse-starlette needed)
```

---

## 11. API ↔ UI Type Contracts

Full TypeScript type for the engine result (mirrors Python `dspy.Prediction` output):

```typescript
// lib/types.ts

export const PramanaType = z.enum(["UPAMANA", "SABDA", "ANUMANA", "PRATYAKSA"])
export const EpistemicStatus = z.enum(["established", "hypothesis", "provisional", "open", "contested"])
export const Label = z.enum(["in", "out", "undecided"])
export const CoverageDecision = z.enum(["FULL", "PARTIAL", "DECLINE"])
export const GroundingMode = z.enum(["minimal", "partial", "full"])
export const AttackType = z.enum(["rebuttal", "undercutting", "undermining"])
export const RuleType = z.enum(["strict", "defeasible"])

export const ProvenanceTagSchema = z.object({
  belief: z.number(),
  disbelief: z.number(),
  uncertainty: z.number(),
  pramana_type: PramanaType,
  source_ids: z.array(z.string()),
  trust_score: z.number(),
  decay_factor: z.number(),
  derivation_depth: z.number().int(),
  timestamp: z.string().optional(),
})

export const ArgumentNodeSchema = z.object({
  id: z.string(),
  conclusion: z.string(),
  rule_type: RuleType,
  label: Label,
  epistemic_status: EpistemicStatus.nullable(),
  tag: ProvenanceTagSchema,
  premises: z.array(z.string()),  // argument IDs
  vyapti_id: z.string().optional(),
})

export const AttackEdgeSchema = z.object({
  id: z.string(),
  attacker: z.string(),
  target: z.string(),
  attack_type: AttackType,
  hetvabhasa: z.string().nullable(),
  specificity_weight: z.number().optional(),
})

export const ProvenanceEntrySchema = z.object({
  sources: z.array(z.string()),
  pramana: PramanaType,
  derivation_depth: z.number().int(),
  trust: z.number(),
  decay: z.number(),
})

export const UncertaintyEntrySchema = z.object({
  total_confidence: z.number(),
  epistemic: z.object({ status: EpistemicStatus }),
  aleatoric: z.number().optional(),
  model: z.number().optional(),
})

export const CoverageResultSchema = z.object({
  coverage_ratio: z.number(),
  matched_predicates: z.array(z.string()),
  unmatched_predicates: z.array(z.string()),
  match_details: z.record(z.string()),
  relevant_vyaptis: z.array(z.string()),
  decision: CoverageDecision,
})

export const ViolationSchema = z.object({
  hetvabhasa: z.string().nullable(),
  type: AttackType,
  attacker: z.string(),
  target: z.string(),
  target_conclusion: z.string(),
})

export const EngineResultSchema = z.object({
  response: z.string(),
  sources: z.array(z.string()),
  uncertainty: z.record(UncertaintyEntrySchema),
  provenance: z.record(ProvenanceEntrySchema),
  violations: z.array(ViolationSchema),
  grounding_confidence: z.number(),
  extension_size: z.number().int(),
  coverage: CoverageResultSchema.nullable(),
  augmentation: z.object({
    augmented: z.boolean(),
    reason: z.string(),
    framework_score: z.number(),
    new_vyapti_count: z.number().int(),
    warnings: z.array(z.string()),
  }).nullable(),
  contestation: z.object({
    mode: z.literal("vada"),
    open_questions: z.array(z.string()),
    suggested_evidence: z.array(z.string()),
  }).nullable(),
  // Argumentation graph (included in full result)
  arguments: z.record(ArgumentNodeSchema),
  attacks: z.array(AttackEdgeSchema),
  labels: z.record(Label),
})

export type EngineResult = z.infer<typeof EngineResultSchema>
export type ArgumentNode = z.infer<typeof ArgumentNodeSchema>
export type AttackEdge = z.infer<typeof AttackEdgeSchema>
// etc.
```

---

## 12. Streaming & Real-time UX

### The problem

The engine takes 1–15 seconds depending on grounding mode. A blank screen for 5 seconds is bad UX for a reasoning tool. The user should see the work happening.

### Solution: SSE stage events + optimistic UI

1. Query is submitted via HTTP POST (returns full result when done).
2. **Simultaneously**, a SSE connection opens to `/api/query/stream`.
3. Each pipeline stage emits an event as it completes.
4. The Pipeline Trace Drawer auto-opens and updates live.
5. The graph renders as soon as the extension stage completes (before synthesis).
6. The response card renders when synthesis completes.
7. The POST response (with full result) arrives last — used as the authoritative state.

### Stage-by-stage UI progression

| Time | Stage event received | UI update |
|------|---------------------|-----------|
| 0ms | Query submitted | QueryInput shows spinner. Trace drawer opens. Stage 1 shows "●○○ Grounding..." |
| ~100ms | `stage:grounding` | Stage 1 ✓. Predicates shown. Stage 2 "●○○ Coverage..." |
| ~105ms | `stage:coverage` | Stage 2 ✓. CoverageIndicator animates to final value. Stage 3 starts. |
| ~115ms | `stage:compilation` | Stage 3 ✓. Graph renders skeleton nodes. Stage 4 starts. |
| ~130ms | `stage:extension` | Stage 4 ✓. Graph nodes color in (IN=green, OUT=red). Graph is interactive now. |
| ~1300ms | `stage:synthesis` | Stage 5 ✓. ResponseCard types in (streaming optional). |
| ~1310ms | `complete` | Full result replaces SSE-partial state. History updated. |

This means the argumentation graph is visible and interactive ~1 second before the text response. Users can inspect the reasoning while waiting for the prose synthesis.

### Text streaming (optional enhancement)

If using an LLM that supports streaming, the synthesis response can be streamed character-by-character. Add a `stage:synthesis_token` event type. `ResponseCard` uses `useEffect` to append tokens progressively. Implement with `dspy.StreamingResponse` or direct API streaming in the backend. Mark as optional in v1.

---

## 13. Implementation Phases

### Phase 1 — Backend foundation (1–2 days)

**Goal:** FastAPI server that can load the engine and answer queries.

Files:
- `backend/main.py` — FastAPI app with routes: `/health`, `/kb/load`, `/kb/inspect`, `/query`
- `backend/engine_state.py` — singleton state: `engine`, `artifacts`, `current_kb_id`
- `backend/models.py` — Pydantic request/response models

Deliverable: `curl -X POST localhost:8000/api/query -d '{"query":"How do unit economics work?"}' | jq` returns a valid EngineResult JSON.

### Phase 2 — SSE pipeline streaming (0.5 days)

**Goal:** SSE endpoint that emits stage events during query execution.

Files:
- `backend/sse_pipeline.py` — async generator wrapping engine pipeline stages

**Implementation pattern (FastAPI native SSE, v0.135+):**

```python
# backend/sse_pipeline.py
from collections.abc import AsyncIterable
from fastapi.sse import ServerSentEvent
import asyncio, json

async def stream_query(query: str, mode: str) -> AsyncIterable[ServerSentEvent]:
    """Runs engine pipeline, yielding SSE events per stage."""
    queue: asyncio.Queue = asyncio.Queue()

    async def run():
        try:
            # Stage 1: Grounding
            grounding = await asyncio.to_thread(engine_state.engine.grounding, query)
            await queue.put(ServerSentEvent(
                event="stage:grounding",
                data=json.dumps({"predicates": grounding.predicates,
                                 "confidence": grounding.confidence,
                                 "mode": mode}),
            ))
            # Stage 2: Coverage
            coverage = await asyncio.to_thread(engine_state.engine.coverage_analyzer.analyze,
                                               grounding.predicates)
            await queue.put(ServerSentEvent(
                event="stage:coverage",
                data=json.dumps(coverage.model_dump()),
            ))
            # ... stages 3–5 similarly ...
            full_result = await asyncio.to_thread(engine_state.engine.forward_with_coverage, query)
            await queue.put(ServerSentEvent(event="complete", data=full_result.model_dump_json()))
        except Exception as e:
            await queue.put(ServerSentEvent(event="error", data=json.dumps({"message": str(e)})))
        finally:
            await queue.put(None)  # sentinel

    asyncio.create_task(run())
    while True:
        event = await queue.get()
        if event is None:
            break
        yield event

# backend/main.py (route)
from fastapi.sse import EventSourceResponse

@app.get("/api/query/stream", response_class=EventSourceResponse)
async def query_stream(query: str, mode: str = "partial"):
    return EventSourceResponse(stream_query(query, mode))
    # FastAPI automatically adds: Cache-Control: no-cache,
    # X-Accel-Buffering: no, keep-alive pings every 15s
```

Deliverable: `curl -N localhost:8000/api/query/stream?query=...` streams stage events.

### Phase 3 — Next.js 15 skeleton + KB select (1 day)

**Goal:** Scaffold project, install all dependencies, landing page with KB select → compile → navigate to studio shell.

**Scaffold commands:**

```bash
# In anvikshiki_ecosystem/
pnpm create next-app@latest webapp \
  --typescript --tailwind --eslint \
  --app --src-dir=false --import-alias="@/*"

cd webapp

# Install shadcn (CLI v4)
pnpm dlx shadcn@latest init
# → style: new-york, base color: neutral, CSS variables: yes

# Add all components
pnpm dlx shadcn@latest add button badge card separator sheet drawer \
  command input textarea label tabs accordion scroll-area \
  dialog tooltip popover progress skeleton table select \
  toggle-group toast sonner hover-card collapsible chart sidebar

# React Flow v12
pnpm add @xyflow/react @dagrejs/dagre

# State + validation
pnpm add zustand zod

# Dev
pnpm add -D @types/dagre
```

Files:
- `webapp/app/page.tsx` — KB select grid
- `webapp/app/studio/page.tsx` — three-column layout shell (no graph yet)
- `webapp/lib/api.ts` — typed fetch wrappers
- `webapp/store/kbStore.ts` — KB state
- `webapp/components/kb/KBSelectCard.tsx`

**Next.js 15 notes:**
- `async` Server Components by default — static panels (KB summary sidebar) are RSC
- Query Studio is `'use client'` — it needs live state
- `next.config.ts` needs `rewrites` to proxy `/api/*` → `http://localhost:8000/*` for local dev (avoids CORS)

Deliverable: Can load a KB from the UI and see the stub studio screen.

### Phase 4 — Query input + result panels (1.5 days)

**Goal:** Submit a query, see text response + provenance table + violations.

Files:
- `webapp/components/query/QueryInput.tsx`
- `webapp/components/query/GroundingModeToggle.tsx`
- `webapp/components/result/ResponseCard.tsx`
- `webapp/components/result/EpistemicStatusBadge.tsx`
- `webapp/components/result/ProvenanceTable.tsx`
- `webapp/components/result/ViolationsPanel.tsx`
- `webapp/components/result/CoverageIndicator.tsx`
- `webapp/store/queryStore.ts`

Deliverable: Full query → response cycle works, all result panels populated.

### Phase 5 — Argumentation graph (2 days)

**Goal:** React Flow graph with custom nodes, edges, dagre layout, node click → provenance sync.

Files:
- `webapp/components/graph/ArgumentationGraph.tsx`
- `webapp/components/graph/ArgumentNode.tsx`
- `webapp/components/graph/AttackEdge.tsx`
- `webapp/lib/graphTransform.ts`

Deliverable: Graph renders correctly for business expert queries, click sync works.

### Phase 6 — Pipeline Trace Drawer + SSE integration (1 day)

**Goal:** Live-updating trace drawer driven by SSE stage events.

Files:
- `webapp/components/trace/PipelineTraceDrawer.tsx`
- `webapp/components/trace/StageCard.tsx`
- `webapp/lib/sse.ts` — `useQueryStream` hook
- `webapp/store/traceStore.ts`

Deliverable: Graph renders on extension event, response on synthesis event. Full streaming UX.

### Phase 7 — KB Inspector + History (1 day)

**Goal:** Full KB inspection + session history.

Files:
- `webapp/components/kb/KBInspectorSheet.tsx`
- `webapp/components/kb/VyaptiRow.tsx`
- `webapp/components/kb/HetvabhasaBadge.tsx`
- History Dialog

Deliverable: All screens functional.

### Phase 8 — Polish (1 day)

- Design tokens finalized, color palette verified in dark + light
- Tooltips on all Sanskrit terms
- Empty states for every panel
- Keyboard shortcuts (⌘K for query, ⌘T for trace drawer)
- Export PNG from graph
- Copy-to-JSON from trace
- `README.md` in `webapp/`

---

## Total Estimate

~8 days of focused engineering, parallelizable (backend and frontend phases 3–4 can run concurrently once Phase 1–2 is done).

---

*End of webapp_design.md — 2026-03-09*
