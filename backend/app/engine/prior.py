"""'Learns from field confirmations' — a count-based local prior.

Each expert confirmation or correction updates a (district, crop, label)
counter. Before the gate, a label's confidence gets a small additive nudge
proportional to its net confirmations in that district, capped at
PRIOR_MAX_BIAS. The cap is below MARGIN and below GATE - FLOOR (asserted in
config), so history alone can never move a prediction across a gate band: the
system cannot become confident because of history rather than evidence.

This is not fine-tuning and not reinforcement learning. It is inspectable
arithmetic, and the bias applied is returned with every diagnosis.
"""

from __future__ import annotations

from dataclasses import replace

from app.config import PRIOR_FULL_COUNT, PRIOR_MAX_BIAS
from app.engine.gate import Prediction, TopK


def bias_for(confirmed: int, corrected: int) -> float:
    net = (confirmed - corrected) / PRIOR_FULL_COUNT
    return PRIOR_MAX_BIAS * max(-1.0, min(1.0, net))


def apply_prior(topk: TopK, counts: dict[str, tuple[int, int]]) -> TopK:
    if not counts:
        return topk
    biased: list[Prediction] = []
    applied: dict[str, float] = {}
    for p in topk.predictions:
        c = counts.get(p.target)
        b = bias_for(*c) if c else 0.0
        if b:
            applied[p.target] = round(b, 4)
        biased.append(Prediction(p.target, min(1.0, max(0.0, p.confidence + b))))
    biased.sort(key=lambda p: p.confidence, reverse=True)
    return replace(topk, predictions=biased, prior_bias=applied)
