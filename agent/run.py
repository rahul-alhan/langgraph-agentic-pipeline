"""CLI entrypoint."""
from __future__ import annotations

import argparse
import json

from .graph import build_graph


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--content", required=True, help="Content to moderate")
    args = p.parse_args()

    graph = build_graph()
    result = graph.invoke({"content": args.content, "audit_log": []})

    print(f"\nFinal decision: {result['final_decision']}")
    print(f"Confidence:     {result['confidence']:.3f}")
    print(f"Needs human:    {result.get('needs_human')}")
    print("\nAudit trail:")
    print(json.dumps(result["audit_log"], indent=2, default=str))


if __name__ == "__main__":
    main()
