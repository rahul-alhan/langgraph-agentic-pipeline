# LangGraph Agentic Pipeline

Stateful multi-agent workflow built on **LangGraph** for content moderation and copyright risk assessment. Demonstrates: tool use, conditional routing, confidence-based guardrails, and human-in-the-loop escalation.

> Mirrors an agent orchestration graph used in a prior production role for a creator-consumer platform.

---

## Agent Graph

```
                       ┌──────────────┐
                       │   PLANNER    │  decompose request
                       └──────┬───────┘
                              ▼
                       ┌──────────────┐
                       │  RETRIEVER   │  fetch policy + IP signals
                       └──────┬───────┘
                              ▼
                       ┌──────────────┐
                       │   ANALYZER   │  classify + score
                       └──────┬───────┘
                              ▼
                       ┌──────────────┐
                       │  GUARDRAIL   │  conf < 0.70 → reject
                       └──────┬───────┘                conf > 0.90 → auto-decision
                              ▼
                   ┌──────────────────┐
                   │  HUMAN ESCALATE  │  conf in [0.70, 0.90]
                   └────────┬─────────┘
                            ▼
                   ┌──────────────────┐
                   │     FINALIZE     │  emit decision + audit trail
                   └──────────────────┘
```

Conditional edges:
- `guardrail → finalize` if confidence ≥ 0.90 or ≤ 0.70
- `guardrail → human_escalate → finalize` otherwise

---

## Quickstart

```bash
pip install -r requirements.txt
# Or `pip install -r requirements-dev.txt` to also get pytest for the suite.

export OPENAI_API_KEY=sk-...

# Run a single moderation request
python -m agent.run --content "Sample creator submission text..."

# Visualize the graph
python -m agent.visualize > graph.mmd
```

---

## Running Tests

```bash
pip install -r requirements-dev.txt
python -m pytest -q
```

The smoke test uses the offline analyzer fallback (no `OPENAI_API_KEY`
required) — it exercises the full graph wiring, guardrail routing, and
the audit log.

---

## State

The graph carries a typed `ModerationState` between nodes:

```python
class ModerationState(TypedDict):
    content: str                    # input
    plan: list[str]                 # planner output
    retrieved: list[dict]           # policy + IP hits
    classification: str             # APPROVE | REJECT | EDIT | ESCALATE
    confidence: float               # 0.0 - 1.0
    needs_human: bool
    human_decision: str | None
    audit_log: list[dict]           # full trace
```

---

## Tools

| Tool | Purpose |
|---|---|
| `policy_search` | retrieve policy snippets relevant to the content |
| `ip_scan` | check against trademarks + fingerprint database |
| `confidence_calibrator` | calibrate raw model score to historical base rates |

All tool calls are logged into `audit_log` with timestamp, args, and result hash.

---

## Repository Layout

```
langgraph-agentic-pipeline/
├── README.md
├── requirements.txt
├── agent/
│   ├── __init__.py
│   ├── state.py             # ModerationState TypedDict
│   ├── tools.py             # tool definitions (mock for demo)
│   ├── nodes.py             # planner, retriever, analyzer, guardrail, ...
│   ├── graph.py             # StateGraph wiring + conditional edges
│   ├── guardrails.py        # confidence thresholds + escalation logic
│   ├── run.py               # CLI entrypoint
│   └── visualize.py         # mermaid export
├── tests/
│   └── test_graph.py
└── examples/
    └── sample_inputs.json
```

---

## Why LangGraph (not just LangChain)

- **Stateful**: pass typed state across nodes, no manual prompt stitching
- **Conditional routing**: `add_conditional_edges` makes guardrail logic a first-class graph primitive
- **Human-in-the-loop**: built-in `interrupt` support — pause graph mid-execution, resume after human input
- **Replayable**: full state snapshots at every step for debugging and auditability

---

## Production Notes

In production this graph is deployed as:
- **AWS Lambda** entry that streams state updates to **DynamoDB** for durability
- **Step Functions** for graph-level retries on transient failures
- **SNS** for human escalation queue (paged to reviewer dashboard)
- **MLflow** for prompt versioning per node

---

## License

MIT
