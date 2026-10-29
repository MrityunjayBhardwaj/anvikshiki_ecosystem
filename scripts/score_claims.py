#!/usr/bin/env python
"""Score a claims-set run against its labels, for Amendment 12 (#230).

    python scripts/score_claims.py traces/occam/run12 traces/occam/run13

Reads each stored question (the artifact and the answer it produced), replays
it, and prints one row per question, then the counts Amendment 12's
predictions are stated in. Nothing here decides an answer. The labels are read
only to print beside each conclusion, and agreement with a label is read by a
person from that printout, not computed: a conclusion is prose, and a
string match on "not" would score the reading this run is meant to test.

What each column counts
───────────────────────
- **fc named / fetched / readable**: review URLs the fact-check search returned,
  the snapshots taken of them, and those with text. A fact-check snapshot is
  one whose URL is among the review URLs in the search's own stored reply.
- **fc quotes**: quote arguments still standing after the support check whose
  span lies in a fact-check snapshot.
- **pairs / neg / num**: the cover pairs a judge was asked about, and how many
  of them the negation veto and the number veto ruled out before any judge.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

from occam.answer import Answer, Artifact, _argued, canonical, replay
from occam.covers import cover_pairs, hosts_of_snapshots
from occam.factcheck import review_urls
from occam.reason import asks_for_a_cause
from occam.snapshot import host

LABELS = Path("occam/questions/claims-1.labels.json")


def fc_urls(artifact: Artifact) -> list[str]:
    """Review URLs from the fact-check search's stored reply, if one was made."""
    out: list[str] = []
    for r in artifact.gather_replies:
        try:
            bodies = json.loads(r)              # the search stores its raw page bodies, as strings
            if not isinstance(bodies, list) or not all(isinstance(b, str) for b in bodies):
                continue
            pages = [json.loads(b) for b in bodies]
        except ValueError:
            continue
        for p in pages:
            out += [u for u in review_urls(p.get("claims", [])) if u not in out]
    return out


def score_one(path: Path) -> dict:
    stored = json.loads(path.read_text())
    art = Artifact.model_validate(stored["artifact"])
    ans = Answer.model_validate(stored["answer"])
    snaps, _, _, argued, _ = _argued(art)
    named = fc_urls(art)
    fc_snaps = [s for s in snaps if set(s.urls) & set(named)]
    fc_ids = {s.id for s in fc_snaps}
    pairs = (cover_pairs(argued, hosts_of_snapshots(snaps), art.params.covers_check)
             if art.params.covers_check >= 2 else ())
    return {
        "q": path.stem, "question": art.question, "status": ans.status.value,
        "abstained": ans.abstained, "replay_ok": canonical(replay(art)) == stored_canonical(stored),
        "conclusion": ans.conclusion, "bound": list(ans.status_bound_by),
        "hosts": sorted({host(s.urls[0]) for s in snaps if s.text.strip()}),
        "cause": asks_for_a_cause(art.question, art.params.why_check),
        "fc_named": len(named), "fc_fetched": len(fc_snaps),
        "fc_readable": sum(bool(s.text.strip()) for s in fc_snaps),
        "fc_quotes": sum(a.kind == "quote" and a.span is not None and a.span.snapshot_id in fc_ids
                         for a in argued.arguments),
        "pairs": len(pairs),
        "neg": sum(p.veto.startswith("negation") for p in pairs),
        "num": sum(p.veto.startswith("the answer states a number") for p in pairs),
    }


def stored_canonical(stored: dict) -> str:
    return canonical(Answer.model_validate(stored["answer"]))


def main(dirs: list[str]) -> int:
    labels = {r["question"]: r for r in json.loads(LABELS.read_text())["rows"]}
    for d in dirs:
        rows = [score_one(p) for p in sorted(Path(d).glob("q*.json"))]
        print(f"\n{d}: {len(rows)} questions")
        for r in rows:
            lab = labels.get(r["question"], {}).get("answer", "?")
            print(f"{r['q']} {lab:<3} {'cause' if r['cause'] else '     '} {r['status']:<11} "
                  f"replay {'ok' if r['replay_ok'] else 'DIFFERS'}  hosts {len(r['hosts'])}  "
                  f"fc {r['fc_named']}/{r['fc_fetched']}/{r['fc_readable']} q{r['fc_quotes']}  "
                  f"pairs {r['pairs']} neg {r['neg']} num {r['num']}")
            print(f"     {r['conclusion'][:150]}")
            print(f"     bound by: {'; '.join(r['bound'])[:200]}")
        est = [r for r in rows if r["status"] == "established"]
        by = lambda lab: [r for r in rows if labels.get(r["question"], {}).get("answer") == lab]
        fetched = sum(r["fc_fetched"] for r in rows)
        unreadable = fetched - sum(r["fc_readable"] for r in rows)
        print(f"established {len(est)} of {len(rows)}; "
              f"no-labelled {sum(r in est for r in by('no'))} of {len(by('no'))}, "
              f"yes-labelled {sum(r in est for r in by('yes'))} of {len(by('yes'))}; "
              f"cause-shaped {sum(r['cause'] for r in est)} of {sum(r['cause'] for r in rows)}")
        print(f"abstained {sum(r['abstained'] for r in rows)}; "
              f"replay differs {sum(not r['replay_ok'] for r in rows)}")
        print(f"questions with a readable fact-check page {sum(r['fc_readable'] > 0 for r in rows)}; "
              f"fact-check snapshots {fetched}, unreadable {unreadable}; "
              f"questions with a standing fact-check quote {sum(r['fc_quotes'] > 0 for r in rows)}")
        print(f"cover pairs {sum(r['pairs'] for r in rows)}, negation veto "
              f"{sum(r['neg'] for r in rows)}, number veto {sum(r['num'] for r in rows)}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
