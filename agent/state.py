from __future__ import annotations

from typing import Annotated, Optional, TypedDict
from operator import add


class ModerationState(TypedDict, total=False):
    content: str
    plan: list[str]
    retrieved: list[dict]
    classification: str           # APPROVE | REJECT | EDIT | ESCALATE
    confidence: float
    needs_human: bool
    human_decision: Optional[str]
    final_decision: str
    audit_log: Annotated[list[dict], add]
