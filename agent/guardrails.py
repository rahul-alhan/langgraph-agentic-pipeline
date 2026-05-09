"""Confidence-based guardrail thresholds."""
from __future__ import annotations

AUTO_APPROVE_MIN = 0.90
AUTO_REJECT_MAX = 0.70


def needs_human_review(confidence: float) -> bool:
    return AUTO_REJECT_MAX < confidence < AUTO_APPROVE_MIN


def auto_decide(confidence: float, raw_label: str) -> str:
    if confidence >= AUTO_APPROVE_MIN:
        return raw_label
    if confidence <= AUTO_REJECT_MAX:
        return "REJECT"
    return "ESCALATE"
