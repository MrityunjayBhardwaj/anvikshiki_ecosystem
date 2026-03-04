# anvikshiki_v4/optimize.py
"""DSPy optimization for the v4 engine."""

import dspy


def calibration_metric_v4(gold, pred) -> float:
    """
    Argumentation-aware calibration metric.
    Rewards: calibration, source attribution, epistemic qualification,
             extension quality, contestation coverage.
    """
    score = 0.0

    # 1. Non-empty, substantive response
    if hasattr(pred, 'response') and pred.response and len(pred.response) > 50:
        score += 0.2

    # 2. Sources cited
    if hasattr(pred, 'sources') and pred.sources:
        score += 0.15

    # 3. Extension quality: productive reasoning occurred
    if hasattr(pred, 'extension_size') and pred.extension_size > 0:
        score += 0.15

    # 4. Epistemic qualification in response
    hedges = ["established", "hypothesis", "provisional",
              "contested", "uncertain", "open question"]
    if hasattr(pred, 'response') and any(
        h in pred.response.lower() for h in hedges
    ):
        score += 0.2

    # 5. Violations reported when present
    if hasattr(pred, 'violations') and pred.violations:
        if hasattr(pred, 'response') and any(
            w in pred.response.lower()
            for w in ["however", "caveat", "exception", "limitation"]
        ):
            score += 0.15

    # 6. No overconfidence
    if hasattr(pred, 'response') and "certainly" not in pred.response.lower():
        score += 0.15

    return min(1.0, score)


def optimize_engine(engine, trainset, valset, auto="medium"):
    """Run MIPROv2 optimization on the engine."""
    optimizer = dspy.MIPROv2(
        metric=calibration_metric_v4,
        auto=auto,
    )
    optimized = optimizer.compile(
        engine,
        trainset=trainset,
        valset=valset,
    )
    return optimized


def evaluate_engine(engine, devset, num_threads=8):
    """Evaluate engine on a development set."""
    evaluator = dspy.Evaluate(
        devset=devset,
        metric=calibration_metric_v4,
        num_threads=num_threads,
        display_progress=True,
    )
    return evaluator(engine)
