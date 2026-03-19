"""Convenience runner for poly engine.

Run: python run_engine.py
"""

from __future__ import annotations

import os
import sys


def _ensure_project_root() -> None:
    root = os.path.dirname(os.path.abspath(__file__))
    if root not in sys.path:
        sys.path.insert(0, root)


def main() -> None:
    _ensure_project_root()
    from polytest.engine.__main__ import main as engine_main

    engine_main()


if __name__ == "__main__":
    main()
