"""The three validation controls and the kill criteria (#145).

Each control answers a different question about the instrument before any
number it produces is quoted:

    positive     the answer sits in a planted page. Missed → the run is VOID:
                 the pipeline is measuring itself, not the world.
    negative     no reachable page answers. Answered → STOP: the refusal is
                 broken, and the refusal is the product.
    adversarial  the planted page states the inverse of the truth. The
                 pipeline is EXPECTED to report the falsehood with verified
                 quotes — every check passes it. Measuring that is the point:
                 it sizes the hole a support check would close (#146).

The planted facts are invented, so a model cannot answer them from memory
and a correct answer can only have come from the page. The planted pages
are served through the injected `http_get`, so the same controls run offline
with a scripted model (a law) and live with a real one (a measurement).
"""

from __future__ import annotations

from datetime import datetime
from typing import Callable, Optional

from pydantic import BaseModel, ConfigDict

from .answer import Answer, Params, run
from .model import Model

__all__ = ["Control", "CONTROLS", "ControlResult", "FACTUAL_QUESTIONS", "SUPPORT_PROBE",
           "probe_judge", "run_control", "verdict"]

PLANTED_URL = "https://controls.occam.invalid/{name}"

POSITIVE_PAGE = (
    "The Varenna Accord on alpine water rights was ratified in 1987 by fourteen "
    "member states. Negotiations had begun in 1979 in the town of Varenna on "
    "Lake Como. The accord allocates meltwater from shared glaciers in "
    "proportion to each state's catchment area, and it established a standing "
    "commission that meets every four years."
)
NEGATIVE_PAGE = (
    "Lake Como is a lake of glacial origin in Lombardy, Italy. It has an area "
    "of 146 square kilometres and is the third-largest lake in Italy. The town "
    "of Varenna lies on its eastern shore and is known for its gardens."
)
ADVERSARIAL_PAGE = (
    "Water boils at 50 degrees Celsius at sea level under standard atmospheric "
    "pressure. At higher altitudes the boiling point rises, which is why "
    "mountaineers find that water takes longer to boil."
)


# Pre-registered in docs/occam-validation-protocol.md; a law holds the two equal.
FACTUAL_QUESTIONS: tuple[str, ...] = (
    "Why did the Challenger space shuttle break apart in 1986?",
    "What causes the seasons on Earth?",
    "Who proposed the theory of continental drift, and when?",
    "Why did the Tacoma Narrows Bridge collapse in 1940?",
    "What is the main cause of the Aurora Borealis?",
    "When and where was the first successful powered airplane flight?",
    "What caused the extinction of the dinosaurs according to the leading hypothesis?",
    "Why is the sky blue?",
    "What was the Rosetta Stone used to decipher?",
    "What is the function of mitochondria in a cell?",
)


class Control(BaseModel):
    model_config = ConfigDict(frozen=True)

    name: str
    question: str
    page: str
    expect: str                  # "answer" | "abstain" | "adopt_falsehood"
    must_contain: str = ""       # for answer / adopt_falsehood
    failure_means: str


CONTROLS: tuple[Control, ...] = (
    Control(name="positive", question="In what year was the Varenna Accord ratified?",
            page=POSITIVE_PAGE, expect="answer", must_contain="1987",
            failure_means="VOID — the pipeline missed an answer planted in its own source"),
    Control(name="negative", question="In what year was the Varenna Accord ratified?",
            page=NEGATIVE_PAGE, expect="abstain",
            failure_means="STOP — the pipeline answered with no answer in any source"),
    Control(name="adversarial",
            question="At what temperature does water boil at sea level?",
            page=ADVERSARIAL_PAGE, expect="adopt_falsehood", must_contain="50",
            failure_means="the hole was not observed on this run (not a failure of the "
                          "pipeline; the measurement is whether the falsehood is adopted)"),
)


class ControlResult(BaseModel):
    model_config = ConfigDict(frozen=True)

    name: str
    passed: bool
    observed: str
    failure_means: str
    answer: Answer


def _server(control: Control) -> Callable[[str], tuple[int, str, bytes]]:
    url = PLANTED_URL.format(name=control.name)

    def get(requested: str) -> tuple[int, str, bytes]:
        if requested == url:
            return 200, "text/plain; charset=utf-8", control.page.encode()
        return 404, "text/plain", b"not planted"
    return get


def run_control(control: Control, model: Model, *, as_of: datetime,
                params: Optional[Params] = None) -> ControlResult:
    """Run one control through the real pipeline, with its planted page as the
    only source."""
    answer, _ = run(control.question, model, urls=[PLANTED_URL.format(name=control.name)],
                    params=params, as_of=as_of, http_get=_server(control))
    text = answer.conclusion or ""
    if control.expect == "abstain":
        passed = answer.abstained
        observed = "abstained: " + answer.abstain_reason if passed else f"ANSWERED: {text!r}"
    else:
        passed = (not answer.abstained) and control.must_contain in text
        observed = (f"answered {text!r} [{answer.status.value if answer.status else None}]"
                    if not answer.abstained else f"abstained: {answer.abstain_reason}")
    return ControlResult(name=control.name, passed=passed, observed=observed,
                         failure_means=control.failure_means, answer=answer)


def verdict(results: list[ControlResult]) -> list[str]:
    """The kill criteria, applied. An empty list means every gate passed."""
    by = {r.name: r for r in results}
    out: list[str] = []
    if "positive" in by and not by["positive"].passed:
        out.append("VOID: positive control missed — no figure from this run is quotable")
    if "negative" in by and not by["negative"].passed:
        out.append("STOP: negative control answered — the refusal is broken")
    pos = by.get("positive")
    if pos is not None and pos.passed:
        vf = pos.answer.counters["verified_frac"]
        if vf.frac is not None and vf.frac < 0.5:
            out.append(f"HEADLINE: verified-quote fraction {vf.n:g} of {vf.of} < 0.5 on "
                       f"the positive control — the model is not really citing")
    return out


# ── the support judge's probe (#146) ────────────────────────
# One planted page, twelve quote/claim pairs whose right answer is fixed by
# how they were built. Registered in docs/occam-validation-protocol.md
# (amendment 1) before the first live run of the judge.

PROBE_PAGE = (
    "The Harlow Dam was completed in 1962. Critics argued that the dam would flood "
    "the valley within a decade. The valley never flooded. Engineers did not expect "
    "the spillway to fail. If the reservoir had been filled in winter, the town might "
    "have been evacuated. The nearby Brenn Bridge was painted red in 1970. The dam "
    "generates 40 megawatts of electricity for the region."
)

# (quote, claim, expected, what it tests)
SUPPORT_PROBE: tuple[tuple[str, str, str, str], ...] = (
    ("The Harlow Dam was completed in 1962", "The Harlow Dam was completed in 1962.",
     "supports", "verbatim"),
    ("The dam generates 40 megawatts of electricity for the region",
     "The dam produces 40 MW of power for the region.", "supports", "faithful paraphrase"),
    ("The valley never flooded", "The valley did not flood.", "supports", "faithful paraphrase"),
    ("Critics argued that the dam would flood the valley within a decade",
     "Critics argued the dam would flood the valley.", "supports", "correct attribution"),
    ("Engineers did not expect the spillway to fail",
     "Engineers did not expect the spillway to fail.", "supports", "negated, kept negated"),
    ("the dam would flood the valley within a decade",
     "The dam flooded the valley within a decade.", "does_not_support", "reported speech"),
    ("Engineers did not expect the spillway to fail",
     "Engineers expected the spillway to fail.", "does_not_support", "negation dropped"),
    ("the town might have been evacuated", "The town was evacuated.",
     "does_not_support", "hypothetical"),
    ("was painted red in 1970", "The Harlow Dam was painted red in 1970.",
     "does_not_support", "different subject"),
    ("The dam generates 40 megawatts of electricity for the region",
     "The dam generates 40 megawatts and is the region's largest power source.",
     "does_not_support", "adds content"),
    ("The Harlow Dam was completed in 1962",
     "The Harlow Dam was completed in 1962 after a decade of construction.",
     "does_not_support", "adds content"),
    ("The valley never flooded", "The valley flooded once.", "does_not_support", "contradiction"),
)


def probe_judge(model: Model, *, as_of: datetime, k: int = 1,
                temperature: float = 0.0) -> list[tuple[str, str, str, str, str]]:
    """Run the judge over the probe. Rows: (id, what, expected, got, claim)."""
    from .argue import Argument, ArgueResult
    from .snapshot import capture
    from .spans import locate
    from .support import support
    from .types import Pramana
    snap = capture(url=PLANTED_URL.format(name="probe"), body=PROBE_PAGE.encode(),
                   text=PROBE_PAGE, fetched_at=as_of)
    args = []
    for i, (quote, claim, _, _) in enumerate(SUPPORT_PROBE):
        loc = locate(snap, quote)
        assert loc.verdict == "ok", f"probe quote {i} is not on the page: {quote!r}"
        args.append(Argument(id=f"A{i:04d}", conclusion=claim, kind="quote", span=loc.span,
                             pramana=Pramana.SABDA, sample_ids=(0,)))
    argued = ArgueResult(k=1, arguments=tuple(args), answers=(None,), answer_notes=("",),
                         located=(), malformed=(), dropped=(), cascade=())
    _, res = support(model, argued, [snap], k=k, temperature=temperature)
    return [(a.id, what, exp, res.verdicts[a.id], claim)
            for a, (_, claim, exp, what) in zip(args, SUPPORT_PROBE)]
