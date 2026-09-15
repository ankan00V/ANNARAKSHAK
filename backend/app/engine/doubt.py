"""Doubt Doctor answer resolution.

When the model is torn between two labels, the farmer is asked ONE physical
question authored in the knowledge base (never generated at runtime). "Yes"
resolves to the cue's `yes_means`, "No" to the other label of the pair, and
"Can't tell" escalates. There is deliberately no tiebreak: an inconclusive
answer never falls back to the higher-confidence label.
"""

from __future__ import annotations

ANSWERS = ("yes", "no", "unknown")


def resolve(cue: dict, answer: str) -> str | None:
    """Return the resolved target, or None meaning escalate."""
    a, b = cue["pair"]
    yes = cue["yes_means"]
    if yes not in (a, b):
        return None
    if answer == "yes":
        return yes
    if answer == "no":
        return b if yes == a else a
    return None
