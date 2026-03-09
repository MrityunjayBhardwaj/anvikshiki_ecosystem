import Link from "next/link";
import { Brain, Database, Layers, Zap } from "lucide-react";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { KBLoader } from "@/components/kb/KBLoader";

const FEATURES = [
  {
    icon: Brain,
    title: "ASPIC+ Argumentation",
    description:
      "Rebuttal, undercutting and undermining attacks. Grounded / preferred / stable extension semantics computed in polynomial time.",
  },
  {
    icon: Layers,
    title: "5-Layer Grounding Defense",
    description:
      "Ontology constraint → grammar decoding → N=5 ensemble consensus → round-trip verification → solver feedback.",
  },
  {
    icon: Database,
    title: "Lattice Datalog",
    description:
      "Defeasible rules compiled to Datalog. Semi-naive evaluation. Subjective Logic (b,d,u) belief propagation via ⊗ tensor product.",
  },
  {
    icon: Zap,
    title: "Nyāya Epistemology",
    description:
      "Pramāṇa hierarchy: PRATYAKSA → ANUMANA → SABDA → UPAMANA. Hetvābhāsa fallacy detection. Vāda contestation protocol.",
  },
];

export default function HomePage() {
  return (
    <div className="min-h-screen bg-background flex flex-col">
      {/* Header */}
      <header className="border-b px-6 py-4 flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="w-8 h-8 rounded-lg bg-primary flex items-center justify-center text-primary-foreground font-mono font-bold text-sm">
            आ
          </div>
          <span className="font-semibold tracking-tight">Ānvīkṣikī</span>
          <Badge variant="secondary" className="text-xs font-mono">
            v0.4.0
          </Badge>
        </div>
        <nav className="flex items-center gap-4 text-sm text-muted-foreground">
          <Link
            href="/studio"
            className="hover:text-foreground transition-colors"
          >
            Query Studio
          </Link>
        </nav>
      </header>

      {/* Hero */}
      <section className="flex-1 flex flex-col items-center justify-center px-6 py-16 text-center gap-8">
        <div className="space-y-3">
          <h1 className="text-4xl font-bold tracking-tight">
            Neurosymbolic Reasoning Engine
          </h1>
          <p className="text-lg text-muted-foreground max-w-2xl">
            ASPIC+ structured argumentation · Subjective Logic belief
            propagation · Lattice Datalog grounded semantics · Nyāya
            epistemology
          </p>
        </div>

        {/* KB Loader card */}
        <div className="w-full max-w-md">
          <KBLoader />
        </div>

        {/* Feature cards */}
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 w-full max-w-3xl">
          {FEATURES.map(({ icon: Icon, title, description }) => (
            <Card key={title} className="text-left">
              <CardHeader className="pb-2">
                <div className="flex items-center gap-2">
                  <Icon className="w-4 h-4 text-muted-foreground" />
                  <CardTitle className="text-sm font-medium">{title}</CardTitle>
                </div>
              </CardHeader>
              <CardContent>
                <CardDescription className="text-xs leading-relaxed">
                  {description}
                </CardDescription>
              </CardContent>
            </Card>
          ))}
        </div>
      </section>
    </div>
  );
}
