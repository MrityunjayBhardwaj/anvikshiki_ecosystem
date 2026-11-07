"""Occam v1, frozen (#264): the pipeline that made run 14.

Calibration (#144) learns how often each shown status is right, and a label
only means something for the pipeline that produced the answer it labels. So
v1 is named here, once, in two halves:

- `V1`, the settings a run records in its artifact. `made_under_v1` lists
  every one an artifact holds that differs, so an artifact from another
  pipeline says so instead of passing for v1. A run handed its pages (a
  control, #279) has no searches to count, so it is compared with v1 at 0 web
  and 0 fact-check sources; the artifact's `given_urls` says it was handed
  them. Such a run is v1's reading of those pages, not v1's gathering, so a
  calibration still refuses it.
- `V1_PROMPTS`, the sha256 of every prompt the model is sent, rendered on the
  fixed inputs in `rendered_prompts`. The text lives in the code and is not
  stored in any artifact, so an edit to it would change what the model is
  asked while every recorded number stayed the same. A law compares the
  rendered prompts with these hashes; a difference is a new version, v2,
  never an edit to v1.

What this does not freeze, said so it is not assumed:
- the model behind the name: kie.ai reports no version for `gemini-3-pro`,
  so the provider can change it under the same name;
- the web: pages change, and only the snapshots an artifact stores pin them;
- `n_sources` (Wikipedia pages per question), which `run` takes as an
  argument and no artifact records — `V1_RUN` holds it for the CLI;
- the deterministic reading of replies, which the rules table already
  versions: a stored v1 artifact replays to its stored answer or it does not,
  and `python -m occam frozen DIR` says which, every time.
"""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from typing import Any

from .answer import Params, recorded_params
from .argue import argue_from_replies, argue_prompt
from .attack import attack_prompt
from .covers import CoverPair, covers_prompt
from .equiv import Pair, equiv_prompt
from .gather import QUERY_PROMPT
from .model import KieModel
from .reason import reason_prompt
from .snapshot import capture
from .support import support_prompt

__all__ = ["V1", "V1_RUN", "V1_PROMPTS", "made_under_v1", "rendered_prompts", "fingerprint"]

# As run 14 recorded them (traces/occam/run14, 20 of 20 artifacts identical),
# with every other field at the default it recorded.
V1 = Params(rules=8, argue_prompt=5, judge_same=True, web_sources=3, factcheck_sources=3,
            web_fill=2, model="kie/gemini-3-pro")

# What `run` is given beside the params, which no artifact records.
V1_RUN: dict[str, Any] = {"n_sources": 3}


def _settings(p: Params) -> dict[str, Any]:
    # Not model_dump: Params serialises only the departures from its rules row.
    return {f: getattr(p, f) for f in Params.model_fields}


def made_under_v1(params: Params, *, given_pages: bool = False) -> list[str]:
    """Each stored setting that differs from v1, as "field: v1 X, this Y".
    Empty means the artifact was made under v1's settings. With `given_pages`,
    v1 is what v1 records when it is handed its pages and searches for none."""
    v1 = recorded_params(V1, V1.model, web=not given_pages, factcheck=not given_pages)
    v1, mine = _settings(v1), _settings(params)
    return [f"{f}: v1 {v1[f]!r}, this {mine[f]!r}" for f in v1 if mine[f] != v1[f]]


# ── the prompts, rendered on fixed inputs ───────────────────────────────

_T0 = datetime(2026, 11, 3, tzinfo=timezone.utc)
_Q = "Why do leaves change colour in autumn?"
_TEXT = ("In autumn the leaves stop making chlorophyll. As the green fades, the "
         "yellow and orange pigments that were there all along become visible.")
_SNAP = capture(url="https://example.org/leaves", body=b"leaves", text=_TEXT, fetched_at=_T0)
# Long enough that argue cuts it at v1's window and support shows only the
# words around the quote, so a change to either cut changes a hash.
_FILLER = "Trees respond to shorter days and cooler nights. " * 500
_LONG_TEXT = _FILLER + _TEXT + " " + _FILLER
if len(_LONG_TEXT) <= V1.max_chars:      # a raise: `python -O` drops asserts (#276)
    raise RuntimeError("the long fixture no longer crosses v1's window, so its hash pins nothing")
_LONG = capture(url="https://example.org/long", body=b"long", text=_LONG_TEXT, fetched_at=_T0)
_STEPS = [
    {"id": "s1", "kind": "quote", "source": 1,
     "quote": "In autumn the leaves stop making chlorophyll.",
     "conclusion": "In autumn the leaves stop making chlorophyll."},
    {"id": "s2", "kind": "inference", "from": ["s1"],
     "conclusion": "Leaves change colour because chlorophyll fades."},
]
_A, _B = "the leaves stop making chlorophyll", "chlorophyll fades in autumn"


class _Sent(KieModel):
    """A kie.ai model that records what it would send and sends nothing."""

    def __init__(self) -> None:
        super().__init__("gemini-3-pro", api_key="unused")
        self.sent: list[dict[str, Any]] = []

    def _post(self, body: dict[str, Any]) -> dict[str, Any]:
        self.sent.append(body)
        return {"choices": [{"message": {"content": "x"}}]}


def rendered_prompts() -> dict[str, str]:
    """Every prompt the pipeline sends, by stage, on the fixed inputs above.
    The model's own calls are rendered through v1's model class, so the
    payload around the text (temperature, the search tool's name) is pinned
    too."""
    argued = argue_from_replies([json.dumps({"answer": "s2", "steps": _STEPS})], [_SNAP])
    quotes = [a for a in argued.arguments if a.kind == "quote"]
    long_steps = [{**_STEPS[0], "source": 2}, {**_STEPS[1], "from": ["s1"]}]
    in_long = argue_from_replies([json.dumps({"answer": "s2", "steps": long_steps})],
                                 [_SNAP, _LONG])
    long_quotes = [a for a in in_long.arguments if a.kind == "quote"]
    if not (long_quotes and long_quotes[0].span.snapshot_id == _LONG.id):
        raise RuntimeError("the quote past the window was not read from the long page")
    out = {
        "query": QUERY_PROMPT.format(question=_Q),
        "argue": argue_prompt(_Q, [_SNAP], V1.max_chars),
        "argue/past the window": argue_prompt(_Q, [_SNAP, _LONG], V1.max_chars),
        "support": support_prompt(quotes, [_SNAP]),
        "support/inside a long page": support_prompt(long_quotes, [_SNAP, _LONG]),
        "attack": attack_prompt(_Q, argued.arguments),
        "reason": reason_prompt(_Q, _A),
    }
    for lens in ("question", "claim"):
        pair = Pair(id="p1", lens=lens, a=_A, b=_B, text_a=_A, text_b=_B)
        for flip in (False, True):
            out[f"same/{lens}/{'flipped' if flip else 'as given'}"] = \
                equiv_prompt(_Q, pair, flip=flip)
    cover = CoverPair(answer=_A, source=_B, text_answer=_A, text_source=_B)
    for flip in (False, True):
        out[f"covers/{'flipped' if flip else 'as given'}"] = covers_prompt(cover, flip=flip)
    m = _Sent()
    m.complete("PROMPT", temperature=0.0)
    m.web_search(_Q, 9)
    out["kie/complete"] = json.dumps(m.sent[0], sort_keys=True)
    out["kie/web_search"] = json.dumps(m.sent[1], sort_keys=True)
    return out


def fingerprint() -> dict[str, str]:
    return {k: hashlib.sha256(v.encode()).hexdigest() for k, v in rendered_prompts().items()}


# Rendered at dc527bc, the commit run 14 ran, and at its successor 80568af:
# all 15 identical.
V1_PROMPTS: dict[str, str] = {
    "query": "faeb37be34cfe96054d0bc2e8be09956c5c3626cf149a4498f24d2ca586b3adc",
    "argue": "4cab74900d9b8f9fcb8a9abdb73ddea1165d345edf121da066b19a79c51d8b3e",
    "argue/past the window": "d951dd722f65b330124ea92dda0a9c467cd3b1ee20b7587c2105e8580db72069",
    "support": "951844e0099e0a0ae411ae2741d6aeb4f3c8a26e2db9cb9bbf8764bb52f55db9",
    "support/inside a long page": "8bb0726298a948fdfe752a31d991529c5e5995ea74559f49995f4923be078a4e",
    "attack": "e388184ce5ef04ce5fba45c43e6b749752b542fa57e5b927f4711f5fabd55fc7",
    "reason": "3441995c2b8bfdcc8cf87103372927f170917de199b9a3133f6cd4ee0d8da866",
    "same/question/as given": "9f24e619f0cae7cb924f674f9cbd5b37cee36f205fab0ed8d15ea5037e81f3b7",
    "same/question/flipped": "8318df76881eb88b548fd60751806fe1abbaf24764d93c4ecf2b93173e6402d7",
    "same/claim/as given": "23abc4d2290f6d6f6df0e26ed594474b616bf3ccd836b7ef761d6f7fcd00a73a",
    "same/claim/flipped": "3266074a3140923e6a3bcba894d12c332d1732df29d5b0d2c639b5b73eb9d468",
    "covers/as given": "aa212342656373cc61a442d421ab2f3932bdb222ca2e8d661d4d4bf67ee9a832",
    "covers/flipped": "58d4832d752582e56f8029f3706774fd57bfbc92d412897865f1338e87787d18",
    "kie/complete": "3683d85f2b99cb88d62eb329eed344d5b27abccead1cabdc3b151b91f0855e1b",
    "kie/web_search": "95b150837d6483d09a9ddba8fb492387861c8735c3bc1adb30f45e680ceea9bc",
}
