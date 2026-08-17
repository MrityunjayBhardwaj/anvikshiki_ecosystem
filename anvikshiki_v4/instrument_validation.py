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

from pathlib import Path
from typing import Optional

import yaml
from pydantic import BaseModel, Field

from .extraction_eval import _best_match_score, _description_overlap, _token_overlap
from .predicate_contrariness import match_veto, text_veto

AGREE = "agree"
DISAGREE = "disagree"
UNJUDGED = ""


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
        description=f"{AGREE!r} or {DISAGREE!r}, filled in by a human",
    )
    note: str = ""

    @property
    def judged(self) -> bool:
        return self.human in (AGREE, DISAGREE)

    @property
    def human_says_match(self) -> Optional[bool]:
        if not self.judged:
            return None
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


def build_decision_sheet(
    gold_names: set[str],
    gold_descriptions: dict[str, str],
    candidates: list[tuple[str, str]],
    threshold: float = 0.5,
    match_on: str = "name",
    near_misses_per_gold: int = 3,
) -> list[MatcherDecision]:
    """Every matcher verdict worth a human's attention, as a judgeable list.

    `candidates` are (name, description) pairs as the extractor produced them.
    """
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
        ranked = sorted(
            candidate_names,
            key=lambda c: _similarity(
                gold, c, gold_descriptions.get(gold, ""),
                candidate_descriptions.get(c, ""), match_on,
            ),
            reverse=True,
        )
        for cand in ranked[:near_misses_per_gold]:
            decisions.append(MatcherDecision(
                gold=gold,
                candidate=cand,
                gold_description=gold_descriptions.get(gold, ""),
                candidate_description=candidate_descriptions.get(cand, ""),
                matcher_says_match=False,
                score=round(_similarity(
                    gold, cand, gold_descriptions.get(gold, ""),
                    candidate_descriptions.get(cand, ""), match_on,
                ), 4),
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


def write_decision_sheet(decisions: list[MatcherDecision], path: str | Path) -> Path:
    """Write the sheet for a human to fill in."""
    path = Path(path)
    payload = {
        "instructions": (
            "For each decision below, set `human:` to 'agree' or 'disagree'. "
            "Judge whether the two predicates mean the same thing, reading the "
            "descriptions — not whether the matcher's reasoning looks sensible. "
            "Leave `human:` empty for anything you are not sure about; unjudged "
            "rows are reported as unjudged and never counted as agreement."
        ),
        "decisions": [d.model_dump() for d in decisions],
    }
    path.write_text(yaml.safe_dump(payload, sort_keys=False, width=100))
    return path


def read_decision_sheet(path: str | Path) -> list[MatcherDecision]:
    data = yaml.safe_load(Path(path).read_text()) or {}
    return [MatcherDecision(**d) for d in data.get("decisions", [])]


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
