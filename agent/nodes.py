"""Graph nodes — each node updates ModerationState."""
from __future__ import annotations

import json
import os
import time

from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI

from .guardrails import auto_decide, needs_human_review
from .state import ModerationState
from .tools import confidence_calibrator, ip_scan, policy_search


def _llm():
    return ChatOpenAI(model="gpt-4o-mini", temperature=0)


def _log(node: str, payload: dict) -> dict:
    return {"node": node, "ts": time.time(), **payload}


def planner(state: ModerationState) -> ModerationState:
    plan = [
        "retrieve_policy_context",
        "scan_for_ip_violations",
        "classify_with_confidence",
        "apply_guardrail",
    ]
    return {"plan": plan, "audit_log": [_log("planner", {"plan": plan})]}


def retriever(state: ModerationState) -> ModerationState:
    policy = policy_search.invoke({"query": state["content"][:200]})
    ip = ip_scan.invoke({"content": state["content"]})
    retrieved = [{"kind": "policy", "data": policy}, {"kind": "ip_scan", "data": ip}]
    return {
        "retrieved": retrieved,
        "audit_log": [_log("retriever", {"n_policies": len(policy), "ip": ip})],
    }


def analyzer(state: ModerationState) -> ModerationState:
    if not os.getenv("OPENAI_API_KEY"):
        # offline deterministic fallback for tests / demos
        ip_hit = any(
            r["kind"] == "ip_scan" and r["data"]["trademark_hit"]
            for r in state["retrieved"]
        )
        label, raw = ("REJECT", 0.96) if ip_hit else ("APPROVE", 0.82)
    else:
        prompt = ChatPromptTemplate.from_messages(
            [
                (
                    "system",
                    "You are a content moderation classifier. Output strict JSON: "
                    '{"label": "APPROVE|REJECT|EDIT", "confidence": <0.0-1.0>}.',
                ),
                (
                    "user",
                    "Content: {content}\n\nPolicies + IP scan:\n{retrieved}\n\n"
                    "Classify and give calibrated confidence.",
                ),
            ]
        )
        chain = prompt | _llm()
        resp = chain.invoke(
            {"content": state["content"], "retrieved": json.dumps(state["retrieved"])}
        )
        try:
            parsed = json.loads(resp.content)
            label, raw = parsed["label"], float(parsed["confidence"])
        except Exception:
            label, raw = "ESCALATE", 0.5

    calibrated = confidence_calibrator.invoke({"raw_score": raw})
    return {
        "classification": label,
        "confidence": calibrated,
        "audit_log": [
            _log("analyzer", {"label": label, "raw": raw, "calibrated": calibrated})
        ],
    }


def guardrail(state: ModerationState) -> ModerationState:
    needs_human = needs_human_review(state["confidence"])
    return {
        "needs_human": needs_human,
        "audit_log": [_log("guardrail", {"needs_human": needs_human})],
    }


def human_escalate(state: ModerationState) -> ModerationState:
    """In production this is an `interrupt` — paused until reviewer responds."""
    decision = state.get("human_decision") or state["classification"]
    return {
        "human_decision": decision,
        "audit_log": [_log("human_escalate", {"decision": decision})],
    }


def finalize(state: ModerationState) -> ModerationState:
    if state.get("needs_human") and state.get("human_decision"):
        final = state["human_decision"]
    else:
        final = auto_decide(state["confidence"], state["classification"])
    return {
        "final_decision": final,
        "audit_log": [_log("finalize", {"final_decision": final})],
    }
