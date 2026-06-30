"""Compatibility wrapper for indexing Nokia release notes.

Prefer:
    nokia-docs index-rn --db docs.db --rn-dir .
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "src"))

from doc_search_engine.rn import (
    index_release_notes,
)
from doc_search_engine.rn import (
    main as _cli_main,
)

DB_PATH = Path("docs.db")
RN_DIR = Path(".")
FAIL_ON_ERROR = False


def main(argv: list[str] | None = None) -> None:
    """Run as CLI, or honor DB_PATH/RN_DIR when imported by legacy callers."""
    if argv is not None:
        _cli_main(argv)
        return
    if Path(sys.argv[0]).resolve() == Path(__file__).resolve():
        _cli_main(sys.argv[1:])
        return
    index_release_notes(DB_PATH, RN_DIR, fail_on_error=FAIL_ON_ERROR)


if __name__ == "__main__":
    main()
