# tests/test_engine_v4.py
import pytest


# ── Unit Tests (no LLM required) ──

def test_engine_initialization():
    """KnowledgeStore loads without error."""
    from anvikshiki_v4.t2_compiler_v4 import load_knowledge_store
    ks = load_knowledge_store("anvikshiki_v4/data/sample_architecture.yaml")
    assert ks is not None
    assert "V01" in ks.vyaptis


def test_compile_and_compute():
    """AF construction + grounded extension produces valid labels."""
    from anvikshiki_v4.t2_compiler_v4 import compile_t2, load_knowledge_store
    from anvikshiki_v4.schema_v4 import Label
    ks = load_knowledge_store("anvikshiki_v4/data/sample_architecture.yaml")
    facts = [{"predicate": "concentrated_ownership", "confidence": 0.9}]
    af = compile_t2(ks, facts)
    labels = af.compute_grounded()
    assert any(lbl == Label.IN for lbl in labels.values())


def test_engine_module_imports():
    """Engine module imports without error (DSPy loaded)."""
    from anvikshiki_v4.engine_v4 import AnvikshikiEngineV4, SynthesizeResponse
    assert AnvikshikiEngineV4 is not None
    assert SynthesizeResponse is not None


def test_optimize_metric():
    """Calibration metric runs on a mock prediction."""
    from anvikshiki_v4.optimize import calibration_metric_v4
    import dspy
    pred = dspy.Prediction(
        response="This is an established hypothesis with some uncertainty.",
        sources=["src1"],
        extension_size=3,
        violations=[],
    )
    score = calibration_metric_v4(None, pred)
    assert score > 0.0
