"""A clarification reads as prose, not as a Python list (#102)."""

import pytest

from anvikshiki_v4.engine_v4 import AnvikshikiEngineV4, clarification_response
from anvikshiki_v4.grounding import GroundingResult
from anvikshiki_v4.t2_compiler_v4 import load_knowledge_store

ENTITY = ("ENTITY: one query named the same subject more than one way (acme: Acme, acme). "
          "The binding decides rule chaining, rebuttal and scope, so these are treated as "
          "different entities and no rule will chain across them.")
LOW = "Grounding confidence too low — requesting clarification"


@pytest.mark.parametrize("warnings, expected", [
    ([ENTITY], f"Clarification needed: {ENTITY}"),
    ([ENTITY, LOW], f"Clarification needed:\n- {ENTITY}\n- {LOW}"),
    ([], "Clarification needed, but grounding gave no reason."),
])
def test_warnings_read_as_sentences(warnings, expected):
    assert clarification_response(warnings) == expected


class _Asks:
    def __init__(self, warnings):
        self.warnings = warnings

    def __call__(self, query):
        return GroundingResult(predicates=["x"], confidence=0.0, disputed=["x"],
                               warnings=self.warnings, clarification_needed=True)


@pytest.mark.parametrize("entry, extra", [("forward", {"retrieved_chunks": ["x"]}),
                                          ("forward_with_coverage", {})])
def test_both_engine_paths_answer_the_user_in_prose(entry, extra):
    ks = load_knowledge_store("anvikshiki_v4/data/business_expert.yaml")
    engine = AnvikshikiEngineV4(knowledge_store=ks, grounding_pipeline=_Asks([ENTITY]))
    result = getattr(engine, entry)(query="Is Acme or acme viable?", **extra)
    assert result.response == f"Clarification needed: {ENTITY}"
    assert "['" not in result.response and "']" not in result.response
