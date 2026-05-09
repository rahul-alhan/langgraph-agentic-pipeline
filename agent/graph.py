"""LangGraph StateGraph wiring."""
from __future__ import annotations

from langgraph.graph import END, START, StateGraph

from .nodes import analyzer, finalize, guardrail, human_escalate, planner, retriever
from .state import ModerationState


def _route_from_guardrail(state: ModerationState) -> str:
    return "human_escalate" if state.get("needs_human") else "finalize"


def build_graph():
    g = StateGraph(ModerationState)

    g.add_node("planner", planner)
    g.add_node("retriever", retriever)
    g.add_node("analyzer", analyzer)
    g.add_node("guardrail", guardrail)
    g.add_node("human_escalate", human_escalate)
    g.add_node("finalize", finalize)

    g.add_edge(START, "planner")
    g.add_edge("planner", "retriever")
    g.add_edge("retriever", "analyzer")
    g.add_edge("analyzer", "guardrail")
    g.add_conditional_edges(
        "guardrail",
        _route_from_guardrail,
        {"human_escalate": "human_escalate", "finalize": "finalize"},
    )
    g.add_edge("human_escalate", "finalize")
    g.add_edge("finalize", END)

    return g.compile()
