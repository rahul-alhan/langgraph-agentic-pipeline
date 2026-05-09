"""Emit Mermaid diagram of the compiled graph."""
from .graph import build_graph


def main():
    g = build_graph()
    print(g.get_graph().draw_mermaid())


if __name__ == "__main__":
    main()
