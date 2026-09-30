"""The same-answer judge's probe (#172): pairs whose right answer is known
before any model sees them. Registered in docs/occam-validation-protocol.md
(amendment 3) before the first live run.

Two sources, neither written by hand as a pair:

    flips   run 2's real answer conclusions, each changed by code in one way
            that makes it say something else. "different" by construction.
              number swapped     every number, +1                  claim lens;
                                 question lens too when the question asks "when"
              "not" inserted     after the first is/are/was/were,  both lenses
                                 in the first clause only
              cause and effect   "A because B" → "B because A"     both lenses,
                reversed         (also "is caused by" …)           on why/cause
                                                                   questions only
              antonym swapped    one word from a fixed list        claim lens only
            Why the lenses differ: under the question lens a changed detail the
            question does not ask about is *allowed* to merge, so a flip is
            labelled for that lens only when it changes what the question asks
            (a date on a "when" question, the cause on a "why" question, the
            main assertion when negated). Antonyms can land on an incidental
            detail ("high-latitude aurora"), so they are claim-lens only.
    paws    PAWS-Wiki, human-labelled paraphrase pairs built from word swaps
            (Zhang, Baldridge & He 2019; © Google LLC, freely usable). 100
            paraphrases + 100 non-paraphrases, seeded draw from the test split.
            Claim lens only: PAWS has no questions.

The flip generator was written by the same hand as the judge's prompt, so the
flips are not held out in the sense PAWS is; their labels are fixed by
construction, not by that hand's judgement. PAWS labels are human, and not
ours; they are also not perfect, which is why its limit is a rate.

Scoring reads stored replies with `equiv_from_replies` — the parser the
pipeline uses — so a probe run can be re-scored offline, and the probe tests
the whole mechanism: veto, both orders, and malformed-means-apart.
"""

from __future__ import annotations

import hashlib
import json
import random
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Literal, Sequence

from pydantic import BaseModel, ConfigDict

from .equiv import EquivResult, Lens, Pair, equiv_from_replies, equiv_prompt, veto
from .model import Model

__all__ = ["ProbePair", "ProbeRun", "flips", "run_conclusions", "flip_pairs", "paws_pairs",
           "run_probe", "fill", "score", "kill_criteria", "PAWS_SHA256", "PAWS_SEED", "PAWS_N"]

Expected = Literal["same", "different"]

# The file is derived once from the Hugging Face copy of PAWS-Wiki
# (google-research-datasets/paws @ 161ece95, labeled_final/test parquet,
# sha256 ae342ff1…) — one JSON object per row, keys sorted. Recorded in
# amendment 3; the loader refuses any other bytes.
PAWS_PATH = Path("traces/occam/paws/labeled_final_test.jsonl")
PAWS_SHA256 = "0e2e68dc4a3e1a6120969c1c042636934cae24549ca5e388bed4df7fcc08405e"
PAWS_SEED = 172
PAWS_N = 100

# Registered limits (amendment 3).
FLIP_WRONG_MERGES_ALLOWED = 0
PAWS_WRONG_MERGES_ALLOWED = 5         # of 100 non-paraphrases

# "due to" is left out: it takes a noun phrase, so swapping it with a clause
# makes a sentence that no longer says anything, rather than the reverse.
CAUSE_MARKERS = (" because ", " is caused by ", " are caused by ",
                 " was caused by ", " were caused by ")
ARTICLES = ("The ", "A ", "An ")
COPULAS = ("is", "are", "was", "were")
ANTONYMS = {
    "more": "less", "less": "more", "shorter": "longer", "longer": "shorter",
    "low": "high", "high": "low", "upper": "lower", "lower": "upper",
    "south": "north", "north": "south", "first": "last", "same": "opposite",
    "produce": "consume", "generate": "consume", "stiffened": "softened",
    "failed": "held", "increase": "decrease", "decrease": "increase",
    "rose": "fell", "fell": "rose", "before": "after", "after": "before",
}
_EDGE = ".,;:!?\"'()"


class ProbePair(BaseModel):
    model_config = ConfigDict(frozen=True)

    pair: Pair
    question: str
    expected: Expected
    source: Literal["flip", "paws"]
    kind: str               # how it was made
    origin: str             # the run 2 question or PAWS row it came from


def _numbers_in(text: str) -> set[str]:
    return {t.strip(_EDGE) for t in text.split() if t.strip(_EDGE).isdigit()}


def flips(question: str, conclusion: str) -> list[tuple[str, str, tuple[Lens, ...]]]:
    """Every flip of one conclusion: (kind, flipped text, lenses it is
    labelled `different` under)."""
    asks = {t.strip(_EDGE) for t in question.casefold().split()}
    words = conclusion.split(" ")
    out: list[tuple[str, str, tuple[Lens, ...]]] = []

    for i, w in enumerate(words):                       # numbers, one at a time
        core = w.strip(_EDGE)
        if core.isdigit():
            changed = words[:i] + [w.replace(core, str(int(core) + 1), 1)] + words[i + 1:]
            lenses: tuple[Lens, ...] = ("claim", "question") if "when" in asks \
                else ("claim",)
            out.append(("number swapped", " ".join(changed), lenses))

    for i, w in enumerate(words):                       # the first copula, negated —
        if any(x.endswith(",") or x.casefold() in ("what", "which", "that", "who")
               for x in words[:i]):                     # in the first clause only, so
            break                                       # it negates the main assertion
        if w.casefold() in COPULAS:
            out.append(("not inserted", " ".join(words[:i + 1] + ["not"] + words[i + 1:]),
                        ("claim", "question")))
            break

    if "why" in asks or any(t.startswith("caus") for t in asks):   # cause/effect, reversed
        hits = [(conclusion.find(m), m) for m in CAUSE_MARKERS if m in conclusion]
        if hits:
            at, m = min(hits)
            a, b = conclusion[:at], conclusion[at + len(m):].rstrip(".")
            frame = a[:a.rfind(", ") + 2] if ", " in a else ""   # "According to X, "
            a = a[len(frame):]
            if a.startswith(ARTICLES):
                a = a[0].lower() + a[1:]
            if a and b:
                b = b[0].lower() + b[1:] if frame and b.startswith(ARTICLES) else b
                head = frame + b if frame else b[0].upper() + b[1:]
                out.append(("cause and effect reversed", f"{head}{m}{a}.",
                            ("claim", "question")))

    seen: set[str] = set()                              # antonyms, one word at a time
    for i, w in enumerate(words):
        parts = w.split("-")
        for j, part in enumerate(parts):
            core = part.strip(_EDGE)
            key = core.casefold()
            if key in ANTONYMS and key not in seen:
                seen.add(key)
                new = ANTONYMS[key]
                if core[:1].isupper():
                    new = new[0].upper() + new[1:]
                changed_parts = parts[:j] + [part.replace(core, new, 1)] + parts[j + 1:]
                changed = words[:i] + ["-".join(changed_parts)] + words[i + 1:]
                out.append(("antonym swapped", " ".join(changed), ("claim",)))
    return out


def run_conclusions(folder: Path) -> list[tuple[str, str, str]]:
    """(origin, question, conclusion) for every distinct surviving answer
    conclusion of the runs stored in `folder` — the texts the question lens
    compares — read by the same path replay uses."""
    from .answer import Artifact, _argued
    out = []
    for f in sorted(folder.glob("q*.json")):
        art = Artifact.model_validate(json.loads(f.read_text())["artifact"])
        _, _, argued, _ = _argued(art)
        by = argued.by_id()
        for c in sorted({by[a].conclusion for a in argued.answers if a}):
            out.append((f.stem, art.question, c))
    return out


def flip_pairs(conclusions: Sequence[tuple[str, str, str]]) -> list[ProbePair]:
    """Flips of (origin, question, conclusion) triples, in a fixed order, one
    pair per flip and lens."""
    out: list[ProbePair] = []
    for origin, question, conclusion in conclusions:
        for kind, flipped, lenses in flips(question, conclusion):
            for lens in lenses:
                pid = f"F{len(out):04d}"
                out.append(ProbePair(
                    pair=Pair(id=pid, lens=lens, a=conclusion, b=flipped, text_a=conclusion,
                              text_b=flipped, veto=veto(conclusion, flipped, lens, question)),
                    question=question, expected="different", source="flip", kind=kind,
                    origin=origin))
    return out


def paws_pairs(path: Path = PAWS_PATH, *, seed: int = PAWS_SEED,
               n: int = PAWS_N) -> list[ProbePair]:
    """n paraphrases and n non-paraphrases, drawn with a fixed seed. Refuses a
    file whose bytes are not the registered ones."""
    raw = path.read_bytes()
    got = hashlib.sha256(raw).hexdigest()
    if got != PAWS_SHA256:
        raise ValueError(f"{path} has sha256 {got}, registered {PAWS_SHA256}")
    rows = [json.loads(line) for line in raw.decode().splitlines() if line.strip()]
    rng = random.Random(seed)
    picked = []
    for label in (1, 0):
        pool = sorted((r for r in rows if r["label"] == label), key=lambda r: r["id"])
        picked += rng.sample(pool, n)
    out = []
    for r in picked:
        a, b = r["sentence1"], r["sentence2"]
        out.append(ProbePair(
            pair=Pair(id=f"W{len(out):04d}", lens="claim", a=a, b=b, text_a=a, text_b=b,
                      veto=veto(a, b, "claim", "")),
            question="", expected="same" if r["label"] == 1 else "different",
            source="paws", kind="paraphrase" if r["label"] == 1 else "non-paraphrase",
            origin=f"paws-wiki test id {r['id']}"))
    return out


class ProbeRun(BaseModel):
    """Everything scoring needs: the pairs with their labels, and every reply
    verbatim, in the order `equiv_from_replies` reads them."""

    model_config = ConfigDict(frozen=True)

    model: str
    as_of: str
    temperature: float
    pairs: tuple[ProbePair, ...]
    replies: tuple[str, ...]
    failures: tuple[tuple[int, str], ...] = ()   # calls that never returned a reply
    filled: tuple[int, ...] = ()                 # calls re-asked later by `fill`
    filled_at: str = ""


def run_probe(model: Model, pairs: Sequence[ProbePair], *, as_of: str,
              temperature: float = 0.0, workers: int = 8, retries: int = 3) -> ProbeRun:
    """Each call fresh and independent — exactly the calls `judge_same` makes,
    X/Y then Y/X for each pair no veto ruled out — run concurrently and put
    back in order. A call that fails after retries is stored as an empty reply
    and listed in `failures`; scoring reads it as unanswered, never as the
    judge keeping a pair apart, and `fill` can ask it again."""
    prompts = _prompts(pairs)
    got = _ask(model, prompts, range(len(prompts)), temperature, workers, retries)
    return ProbeRun(model=model.name, as_of=as_of, temperature=temperature,
                    pairs=tuple(pairs), replies=tuple(got[i][0] for i in range(len(prompts))),
                    failures=tuple((i, got[i][1]) for i in range(len(prompts)) if got[i][1]))


def fill(model: Model, run: ProbeRun, *, at: str, workers: int = 2,
         retries: int = 3) -> ProbeRun:
    """Ask again only the calls that never returned a reply — failed, or
    stored empty — with the same prompts, model and temperature. Every reply
    that was returned is kept byte for byte, so nothing already judged can
    change; the calls re-asked are listed in `filled`."""
    if model.name != run.model:
        raise ValueError(f"run was made by {run.model!r}; filling it with {model.name!r} "
                         f"would mix two judges in one figure")
    prompts = _prompts(run.pairs)
    if len(prompts) != len(run.replies):
        raise ValueError(f"{len(run.replies)} stored replies for {len(prompts)} prompts")
    todo = sorted({i for i, _ in run.failures} |
                  {i for i, r in enumerate(run.replies) if not r.strip()})
    got = _ask(model, prompts, todo, run.temperature, workers, retries)
    replies = list(run.replies)
    for i in todo:
        replies[i] = got[i][0]
    return run.model_copy(update={
        "replies": tuple(replies),
        "failures": tuple((i, got[i][1]) for i in todo if got[i][1]),
        "filled": tuple(sorted(set(run.filled) | set(todo))), "filled_at": at})


def _prompts(pairs: Sequence[ProbePair]) -> list[str]:
    """One function for a run and its fill, so a re-asked call is the call
    that was asked."""
    return [equiv_prompt(pp.question, pp.pair, flip=flip)
            for pp in pairs if not pp.pair.veto for flip in (False, True)]


def _ask(model: Model, prompts: Sequence[str], which, temperature: float, workers: int,
         retries: int) -> dict[int, tuple[str, str]]:
    """{call index: (reply, error)} for the calls in `which`."""
    def call(i: int) -> tuple[str, str]:
        err = ""
        for attempt in range(retries):
            try:
                return model.complete(prompts[i], temperature=temperature), ""
            except Exception as e:                      # noqa: BLE001 — recorded, not hidden
                err = str(e)[:300]
                time.sleep(2 ** attempt)
        return "", err

    which = list(which)
    with ThreadPoolExecutor(max_workers=workers) as ex:
        return dict(zip(which, ex.map(call, which)))


def _unanswered(run: ProbeRun) -> set[str]:
    """Pair ids with at least one call that never returned a reply: one that
    failed, or one whose stored reply is empty. The second is read from the
    stored bytes, not from `failures`, so a run made before empty replies
    were refused (#175) is scored the same way as one made after."""
    failed = {i for i, _ in run.failures} | {i for i, r in enumerate(run.replies)
                                             if not r.strip()}
    out, k = set(), 0
    for pp in run.pairs:
        if not pp.pair.veto:
            if k in failed or k + 1 in failed:
                out.add(pp.pair.id)
            k += 2
    return out


def score(run: ProbeRun) -> tuple[EquivResult, list[dict]]:
    """Rows by (source, lens, expected, kind), each with its own denominator.
    `unanswered` pairs are counted apart and excluded from `judged`, so a
    network failure never reads as the judge keeping a pair apart."""
    res = equiv_from_replies(run.replies, [pp.pair for pp in run.pairs])
    lost = _unanswered(run)
    rows: dict[tuple, dict] = {}
    for pp, v in zip(run.pairs, res.verdicts):
        key = (pp.source, pp.pair.lens, pp.expected, pp.kind)
        r = rows.setdefault(key, dict(source=pp.source, lens=pp.pair.lens,
                                      expected=pp.expected, kind=pp.kind, pairs=0, vetoed=0,
                                      unanswered=0, judged=0, merged=0, apart=0,
                                      cannot_tell=0, orders_disagree=0, malformed=0,
                                      merged_ids=[]))
        r["pairs"] += 1
        if pp.pair.veto:
            r["vetoed"] += 1
            continue
        if pp.pair.id in lost:
            r["unanswered"] += 1
            continue
        r["judged"] += 1
        if v.same:
            r["merged"] += 1
            r["merged_ids"].append(pp.pair.id)
        else:
            r["apart"] += 1
        if "cannot_tell" in (v.forward, v.backward):
            r["cannot_tell"] += 1
        if v.forward and v.backward and v.forward != v.backward:
            r["orders_disagree"] += 1
        if v.forward is None or v.backward is None:
            r["malformed"] += 1
    return res, list(rows.values())


def kill_criteria(rows: Sequence[dict]) -> list[str]:
    """The registered limits, applied. Wrong merges count over expected-
    `different` pairs, veto included in the denominator: the veto is part of
    the mechanism being tested."""
    out = []
    flip_wrong = sum(r["merged"] for r in rows if r["source"] == "flip"
                     and r["expected"] == "different")
    if flip_wrong > FLIP_WRONG_MERGES_ALLOWED:
        out.append(f"STOP: {flip_wrong} code-generated flip(s) merged with the original")
    neg = [r for r in rows if r["source"] == "paws" and r["expected"] == "different"]
    paws_wrong = sum(r["merged"] for r in neg)
    if paws_wrong > PAWS_WRONG_MERGES_ALLOWED:
        out.append(f"STOP: {paws_wrong} of {sum(r['pairs'] for r in neg)} PAWS "
                   f"non-paraphrases merged (limit {PAWS_WRONG_MERGES_ALLOWED})")
    lost = sum(r["unanswered"] for r in rows if r["expected"] == "different")
    if lost:
        out.append(f"INCOMPLETE: {lost} expected-different pair(s) never answered — "
                   f"the limits above cannot clear until they are")
    return out
