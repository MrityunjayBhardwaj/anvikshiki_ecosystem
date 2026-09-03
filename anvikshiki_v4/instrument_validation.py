# anvikshiki_v4/instrument_validation.py
"""Checking the matcher against human judgment, before any number is reported.

The harness grades extraction. Nothing grades the harness. Until something
does, a precision figure means "the matcher said so" and not "this is right" —
and the matcher previously said an extractor emitting the exact inverse of
every gold predicate scored 1.000/1.000.

This is the step the field took when CaRB replaced OIE2016: the two benchmarks
produced contradictory system rankings on the same systems, and human
assessment was what settled which benchmark to believe. A loose matcher does
not add noise to a measurement. It inverts the conclusion.

What is judged, and why not everything
──────────────────────────────────────
Fourteen gold predicates against roughly thirty candidates is about 420 pairs,
which nobody will judge carefully and which mostly consist of obviously
unrelated strings. The sheet therefore carries the pairs where the matcher's
verdict could be wrong in a way that changes a reported number:

  * every pair the matcher MATCHED — each one is a precision claim
  * for every gold predicate the matcher matched to nothing, its nearest
    candidates — each one a possible missed match, and therefore a recall claim

That second half is the half a review interface built around extractor output
cannot produce. The HITL reviewer shows only what the extractor proposed and
offers accept/reject/modify, so it can find false positives and is
structurally blind to false negatives — which is what recall is made of.

What the disagreements decide
─────────────────────────────
The two disagreement classes are not symmetric, and conflating them is how a
dependency gets bought that was never needed:

  * matcher says yes, human says no → a precision failure. The veto is the
    instrument for this, and it is cheap.
  * matcher says no, human says yes → the only evidence that token overlap is
    insufficient, and therefore the only evidence that a semantic encoder
    would earn its cost. If this class is empty, it would not.
"""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

import yaml
from pydantic import BaseModel, Field

from .extraction_eval import _best_match_score, _description_overlap, _token_overlap
from .predicate_contrariness import match_veto, text_veto

# What a human writes in `human:`.
#
# MATCH / NO_MATCH state a fact about the two predicates. AGREE / DISAGREE
# state a relation to the matcher's verdict, and that is the problem they were:
# on a `near_miss` row `matcher_says_match` is False, so "these two mean the
# same thing" had to be entered as `disagree`. Thirty-three of the shipped
# sheet's thirty-eight rows are near misses, and the instruction printed at the
# top of the sheet asks the judge for the fact — so answering the question as
# asked inverted almost every row, silently and undetectably.
#
# The relative pair is still read, because a sheet already written in it means
# exactly what it meant. Nothing registered depends on the spelling: every
# quantity in the pre-registration is computed from `human_says_match`, which
# is derived either way — `replay_mode` has always had to derive it, because a
# verdict that flips under a mode switch would otherwise rewrite what the human
# said.
MATCH = "match"
NO_MATCH = "no_match"
AGREE = "agree"
DISAGREE = "disagree"
UNJUDGED = ""

JUDGMENTS = (MATCH, NO_MATCH, AGREE, DISAGREE)


class MatcherDecision(BaseModel):
    """One matcher verdict a human is asked to confirm or overturn."""

    gold: str
    candidate: str
    gold_description: str = ""
    candidate_description: str = ""
    matcher_says_match: bool
    score: float = 0.0
    veto_reason: str = ""
    kind: str = Field(
        default="matched",
        description="'matched' (a precision claim) or 'near_miss' (a recall claim)",
    )
    human: str = Field(
        default=UNJUDGED,
        description=(
            f"{MATCH!r} or {NO_MATCH!r} — a fact about the two predicates, "
            f"filled in by a human. {AGREE!r} and {DISAGREE!r} are also read, "
            f"relative to `matcher_says_match`, for sheets written before the "
            f"vocabulary said what it meant."
        ),
    )
    note: str = ""

    @property
    def judged(self) -> bool:
        return self.human in JUDGMENTS

    @property
    def human_says_match(self) -> Optional[bool]:
        """What the human said about the pair, however they spelled it.

        The one quantity every registered figure is computed from. Stating it
        directly is what the fact vocabulary buys; the relative one is resolved
        against the verdict the row carried when it was judged.
        """
        if not self.judged:
            return None
        if self.human == MATCH:
            return True
        if self.human == NO_MATCH:
            return False
        return (
            self.matcher_says_match
            if self.human == AGREE
            else not self.matcher_says_match
        )


class AgreementReport(BaseModel):
    """How far the matcher and the human agree, and where they do not."""

    judged: int = 0
    unjudged: int = 0
    both_match: int = 0
    both_reject: int = 0
    matcher_only: int = 0          # matcher yes, human no — precision failure
    human_only: int = 0            # matcher no, human yes — semantics needed
    observed_agreement: Optional[float] = None
    cohens_kappa: Optional[float] = None
    kappa_undefined_reason: str = ""

    @property
    def semantic_encoder_is_indicated(self) -> Optional[bool]:
        """Whether any evidence exists that token overlap is insufficient.

        None when nothing was judged. A semantic encoder is an untested
        dependency until this is True, and `human_only` is the only class of
        disagreement that argues for one.
        """
        if not self.judged:
            return None
        return self.human_only > 0


class MatcherParams(BaseModel):
    """The matcher settings that decide which rows land on the sheet.

    Grouped into one object so the sheet can record exactly what built it.
    Passing these as loose keyword arguments meant the caller had to restate
    them for the provenance block, and anything the caller left on its default
    had to be restated as a literal — which goes stale the moment the default
    moves. One object is passed to the matcher and written to the sheet, so
    the two cannot drift apart.

    `match_on` defaults to 'name' as registered in
    `discussions/instrument-validation-preregistration.md`; the registered
    protocol changes that default only if human judgments favour another mode.
    """

    match_on: str = "name"
    threshold: float = 0.5
    near_misses_per_gold: int = 3


def build_decision_sheet(
    gold_names: set[str],
    gold_descriptions: dict[str, str],
    candidates: list[tuple[str, str]],
    params: Optional[MatcherParams] = None,
) -> list[MatcherDecision]:
    """Every matcher verdict worth a human's attention, as a judgeable list.

    `candidates` are (name, description) pairs as the extractor produced them.
    """
    params = params or MatcherParams()
    threshold = params.threshold
    match_on = params.match_on
    near_misses_per_gold = params.near_misses_per_gold

    candidate_names = {name for name, _ in candidates}
    candidate_descriptions = {name: desc for name, desc in candidates}

    decisions: list[MatcherDecision] = []
    matched_gold: set[str] = set()

    for cand_name, cand_desc in candidates:
        for gold in sorted(gold_names):
            score = _best_match_score(
                cand_name, {gold}, threshold,
                match_on=match_on,
                subject_description=cand_desc,
                candidate_descriptions=gold_descriptions,
            )
            if score > 0:
                matched_gold.add(gold)
                decisions.append(MatcherDecision(
                    gold=gold,
                    candidate=cand_name,
                    gold_description=gold_descriptions.get(gold, ""),
                    candidate_description=cand_desc,
                    matcher_says_match=True,
                    score=round(score, 4),
                    kind="matched",
                ))

    # Recall side: for gold nothing matched, the nearest candidates. Without
    # these the sheet can only find false positives, and recall would be
    # judged by the same blindness it is meant to measure.
    for gold in sorted(gold_names - matched_gold):
        # Rank on (-similarity, name), which is a TOTAL order because candidate
        # names are unique. Ranking on similarity alone is not: `sorted` is
        # stable, so tied candidates keep the order of the collection they came
        # from — and that collection is a set, whose iteration order for strings
        # is randomised per process by PYTHONHASHSEED. Ties are not an edge case
        # here. Under match_on='name' most pairs score exactly 0.0, so which
        # near misses a human is asked to judge changed from run to run, and the
        # sheet could not be regenerated to match the judgments stored against
        # it. Scoring once and carrying the score also guarantees the number
        # written is the number ranked on.
        ranked = sorted(
            (
                (
                    _similarity(
                        gold, cand, gold_descriptions.get(gold, ""),
                        candidate_descriptions.get(cand, ""), match_on,
                    ),
                    cand,
                )
                for cand in candidate_names
            ),
            key=lambda scored: (-scored[0], scored[1]),
        )
        for score, cand in ranked[:near_misses_per_gold]:
            decisions.append(MatcherDecision(
                gold=gold,
                candidate=cand,
                gold_description=gold_descriptions.get(gold, ""),
                candidate_description=candidate_descriptions.get(cand, ""),
                matcher_says_match=False,
                score=round(score, 4),
                veto_reason=(
                    match_veto(cand, gold)
                    or text_veto(
                        candidate_descriptions.get(cand, ""),
                        gold_descriptions.get(gold, ""),
                    )
                    or ""
                ),
                kind="near_miss",
            ))

    return decisions


def _similarity(
    gold: str, candidate: str,
    gold_description: str, candidate_description: str,
    match_on: str,
) -> float:
    """Raw similarity, ignoring the veto — what the matcher saw before refusing."""
    scores = []
    if match_on in ("name", "either"):
        scores.append(_token_overlap(candidate, gold))
    if match_on in ("description", "either") and gold_description and candidate_description:
        scores.append(_description_overlap(candidate_description, gold_description))
    return max(scores) if scores else 0.0


class SheetProvenance(BaseModel):
    """How this sheet was built — enough to regenerate exactly this sheet.

    The registered protocol requires the model, the candidate count and the
    match mode to be reported alongside every figure. They used to be printed
    to stdout and nowhere else, so they survived only as long as a terminal
    scrollback, and the sheet on disk could not say which of the three modes
    had chosen its rows.

    That matters more than record-keeping. Judgments are stored per (gold,
    candidate) row, so a sheet regenerated under different parameters no longer
    corresponds to the judgments already entered against it. A kill criterion
    computed over a pairing nobody can reproduce is not checkable.

    The identity fields carry no defaults deliberately: a half-written block
    must fail loudly rather than describe a run that did not happen.
    """

    matcher: MatcherParams
    extraction_model: str = Field(
        description=(
            "The model that produced the candidates. Never a stand-in like "
            "'(cached)': the sheet's whole purpose is to say what produced it, "
            "and an unknown model must read as unknown."
        ),
    )
    extraction_sha256: str = Field(
        description="SHA-256 of the Stage A output the candidates were read from.",
    )
    chapter_id: str
    gold_count: int
    candidate_count: int
    matched_rows: int
    near_miss_rows: int
    git_commit: str = Field(
        description=(
            "Code version that built the sheet, with a '-dirty' suffix when the "
            "tree had uncommitted changes — a sheet built from uncommitted code "
            "cannot be regenerated from the commit alone."
        ),
    )
    python_hash_seed: str = Field(
        description=(
            "Recorded because set-iteration order once decided which rows "
            "reached this sheet. The ranking is a total order now, so this "
            "should no longer change the output — recording it is what lets a "
            "reader confirm that rather than take it on trust."
        ),
    )
    built_at: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat(timespec="seconds"),
    )


class DecisionSheet(BaseModel):
    """A sheet as it sits on disk: the rows, and what built them.

    `provenance` is optional only so that sheets written before it existed
    still load. It is `None` for those — never a plausible-looking default,
    which would describe a build that never happened and would be
    indistinguishable from a real record of one.
    """

    decisions: list[MatcherDecision] = Field(default_factory=list)
    provenance: Optional[SheetProvenance] = None


def write_decision_sheet(
    decisions: list[MatcherDecision],
    path: str | Path,
    provenance: SheetProvenance,
) -> Path:
    """Write the sheet for a human to fill in.

    `provenance` is required rather than optional: made skippable, it would be
    skipped, and the sheet would again be a set of rows nobody can trace to the
    run that produced them.
    """
    path = Path(path)
    payload = {
        "instructions": (
            "For each decision below, set `human:` to 'match' if the two "
            "predicates mean the same thing and 'no_match' if they do not. "
            "Judge the pair by reading the descriptions. Ignore "
            "`matcher_says_match`, `score` and `kind`: those are what is being "
            "measured, and a judgment copied back from them measures nothing. "
            "Leave `human:` empty for anything you are unsure about; unjudged "
            "rows are reported as unjudged and never counted either way. "
            "`scripts/judge_decision_sheet.py` asks the same question one pair "
            "at a time, in a shuffled order and without showing you the "
            "matcher's verdict."
        ),
        "provenance": provenance.model_dump(),
        "decisions": [d.model_dump() for d in decisions],
    }
    path.write_text(yaml.safe_dump(payload, sort_keys=False, width=100))
    return path


def read_decision_sheet(path: str | Path) -> DecisionSheet:
    """Load a sheet, with `provenance=None` when the file records none."""
    data = yaml.safe_load(Path(path).read_text()) or {}
    raw_provenance = data.get("provenance")
    return DecisionSheet(
        decisions=[MatcherDecision(**d) for d in data.get("decisions", [])],
        provenance=SheetProvenance(**raw_provenance) if raw_provenance else None,
    )


def replay_mode(
    decisions: list[MatcherDecision],
    gold_descriptions: dict[str, str],
    match_on: str,
    threshold: float = 0.5,
) -> list[MatcherDecision]:
    """Re-run the matcher over judged pairs under a different match mode.

    A human judges whether two predicates mean the same thing, which is a fact
    about the pair and not about the matcher. So one set of judgments scores
    every mode, and the modes are compared on identical ground rather than each
    being judged against a sheet built to flatter it.

    What the human said is carried across unchanged; only the matcher's
    verdict is recomputed. It is rewritten into the fact vocabulary on the way
    through, which is what makes "unchanged" true by construction: a stored
    agree/disagree means something different once the verdict beneath it moves,
    so replaying it required a compensating flip, and a compensating flip is
    only ever as reliable as the person maintaining it.
    """
    replayed: list[MatcherDecision] = []
    for d in decisions:
        truth = d.human_says_match
        score = _best_match_score(
            d.candidate, {d.gold}, threshold,
            match_on=match_on,
            subject_description=d.candidate_description,
            candidate_descriptions={d.gold: gold_descriptions.get(d.gold, "")},
        )
        says_match = score > 0
        replayed.append(d.model_copy(update={
            "matcher_says_match": says_match,
            "score": round(score, 4),
            "human": (
                UNJUDGED if truth is None else (MATCH if truth else NO_MATCH)
            ),
        }))
    return replayed


def agreement(decisions: list[MatcherDecision]) -> AgreementReport:
    """Agreement between matcher and human, with Cohen's kappa.

    Unjudged rows are counted and excluded, never treated as agreement. A sheet
    nobody filled in must not report perfect agreement, which is the same
    defect as a validation that never ran scoring 1.0.
    """
    judged = [d for d in decisions if d.judged]
    report = AgreementReport(
        judged=len(judged),
        unjudged=len(decisions) - len(judged),
    )
    if not judged:
        report.kappa_undefined_reason = "nothing was judged"
        return report

    for d in judged:
        if d.matcher_says_match and d.human_says_match:
            report.both_match += 1
        elif not d.matcher_says_match and not d.human_says_match:
            report.both_reject += 1
        elif d.matcher_says_match:
            report.matcher_only += 1
        else:
            report.human_only += 1

    n = len(judged)
    report.observed_agreement = (report.both_match + report.both_reject) / n

    matcher_yes = (report.both_match + report.matcher_only) / n
    human_yes = (report.both_match + report.human_only) / n
    expected = matcher_yes * human_yes + (1 - matcher_yes) * (1 - human_yes)

    if abs(1.0 - expected) < 1e-12:
        report.kappa_undefined_reason = (
            "both raters gave the same answer to everything, so chance "
            "agreement is 1.0 and kappa is undefined — the observed agreement "
            "is the whole result"
        )
    else:
        report.cohens_kappa = (report.observed_agreement - expected) / (1 - expected)

    return report
