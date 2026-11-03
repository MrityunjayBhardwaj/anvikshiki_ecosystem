# tests/test_headline_is_not_a_verdict.py
"""A yes or no heading the answer is not the engine's verdict (#197).

The engine derives conclusions, not a verdict on the question: nothing records
which fact a yes/no question asks about. So the "No" that headed the growth
answer ("Is growth alone enough to make a business viable?") was the
synthesizer's reading, and it drifted from run to run. Until a verdict is
derived, the answer says so.

The openings below are the synthesizer's own, from six live runs of the growth
question (openrouter/z-ai/glm-5.2, shipped business base, 2026-10-31 to
2026-11-03; traces/premise-195-197/*/growth.json).
"""

import dspy
import pytest

from anvikshiki_v4.engine_v4 import AnvikshikiEngineV4, headline_notice
from anvikshiki_v4.grounding import GroundingResult
from anvikshiki_v4.t2_compiler_v4 import load_knowledge_store

BUSINESS = "anvikshiki_v4/data/business_expert.yaml"
GROWTH = ("organizational_growth(business)",)
NOTICE = "Note: my knowledge base does not decide yes or no here."


@pytest.mark.parametrize("text, word", [
    # live
    ("No — growth by itself is not enough to make a business viable", "No"),
    ("No — based on the reasoning derived from the knowledge base", "No"),
    ("Short answer: no — and this holds even granting the question's premise", "No"),
    # the same, dressed
    ("**No.** Growth alone is not enough.", "No"),
    ("> **Short answer:** No, growth alone is not enough.", "No"),
    ("In short, yes.", "Yes"),
    ("Yes, it is.", "Yes"),
    ("no", "No"),
])
def test_a_leading_yes_or_no_is_named(text, word):
    notice = headline_notice(text)
    assert notice.startswith(NOTICE)
    assert f'The "{word}" that opens the answer' in notice


@pytest.mark.parametrize("text", [
    # live
    "The derived reasoning suggests that growth alone is not enough",
    # a word that starts with no/yes, or a yes/no that isn't a verdict
    "No one can say from the base alone.",
    "Not necessarily: growth helps but",
    "Nobody in the base derives viability.",
    "None of the derived conclusions bear on it.",
    "Yes and no: growth helps but",
    "Notably, no rule derives viability.",
    "Answering this: no rule derives it.",
    "Short answer — not quite.",
    "",
])
def test_anything_else_is_left_alone(text):
    assert headline_notice(text) is None


class _Grounding:
    def __init__(self, predicates):
        self._result = GroundingResult(
            predicates=list(predicates), confidence=1.0, disputed=[],
            warnings=[], advisories=[], clarification_needed=False,
        )

    def __call__(self, query):
        return self._result


def _run(model_text, path):
    engine = AnvikshikiEngineV4(
        knowledge_store=load_knowledge_store(BUSINESS),
        grounding_pipeline=_Grounding(GROWTH))
    engine.synthesizer = lambda **kw: dspy.Prediction(
        response=model_text, sources_cited=[])
    return (engine.forward("q", retrieved_chunks=[]) if path == "forward"
            else engine.forward_with_coverage("q"))


@pytest.mark.parametrize("path", ["forward", "forward_with_coverage"])
def test_the_answer_says_its_no_is_not_the_engines(path):
    text = "No — growth alone is not enough to make a business viable."
    blocks = _run(text, path).response.split("\n\n")
    assert blocks[-1] == text
    assert blocks[-2].startswith(NOTICE)


@pytest.mark.parametrize("path", ["forward", "forward_with_coverage"])
def test_no_notice_when_the_answer_does_not_lead_with_one(path):
    text = "The derived reasoning suggests growth alone is not enough."
    assert NOTICE not in _run(text, path).response
