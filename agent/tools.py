"""Mock tools — replace with real services in production."""
from __future__ import annotations

import hashlib
from langchain_core.tools import tool


@tool
def policy_search(query: str) -> list[dict]:
    """Retrieve policy snippets relevant to the moderation query."""
    snippets = [
        {
            "policy_id": "POL-001",
            "text": "Copyright similarity > 0.85 escalates within 24h.",
            "score": 0.92,
        },
        {
            "policy_id": "POL-014",
            "text": "Confidence < 0.70 results in rejection with audit log.",
            "score": 0.81,
        },
    ]
    return [s for s in snippets if any(t in query.lower() for t in s["text"].lower().split()[:3])] or snippets[:1]


@tool
def ip_scan(content: str) -> dict:
    """Check content against trademarks + fingerprint database."""
    digest = hashlib.sha256(content.encode()).hexdigest()
    has_hit = digest[0] in "0123"
    return {
        "trademark_hit": has_hit,
        "fingerprint_similarity": 0.42 if not has_hit else 0.91,
        "checked_at": "2026-01-01T00:00:00Z",
    }


@tool
def confidence_calibrator(raw_score: float, base_rate: float = 0.12) -> float:
    """Calibrate raw model score against historical base rates."""
    if raw_score >= 0.95:
        return min(0.98, raw_score)
    return max(0.0, min(1.0, raw_score * (1 - 0.5 * (1 - base_rate))))


TOOLS = [policy_search, ip_scan, confidence_calibrator]
