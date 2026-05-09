"""Smoke tests for the moderation graph (use offline analyzer fallback)."""
from __future__ import annotations

import os

os.environ.pop("OPENAI_API_KEY", None)

from agent.graph import build_graph
from agent.guardrails import auto_decide, needs_human_review


def test_high_confidence_skips_human():
    assert needs_human_review(0.95) is False
    assert needs_human_review(0.5) is False
    assert needs_human_review(0.8) is True


def test_auto_decide():
    assert auto_decide(0.95, "APPROVE") == "APPROVE"
    assert auto_decide(0.6, "APPROVE") == "REJECT"
    assert auto_decide(0.8, "APPROVE") == "ESCALATE"


def test_graph_runs_end_to_end():
    g = build_graph()
    out = g.invoke({"content": "Some safe creator post about hiking trails.", "audit_log": []})
    assert "final_decision" in out
    assert out["final_decision"] in {"APPROVE", "REJECT", "EDIT", "ESCALATE"}
    assert len(out["audit_log"]) >= 5
