"""Compatibility wrapper for re-indexing Nokia release notes.

Prefer:
    doc-search reindex-rn --db docs.db --rn-dir .
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "src"))

from doc_search_engine.rn import reindex_release_notes


def main() -> None:
    parser = argparse.ArgumentParser(description="Remove old RN rows and re-index release notes.")
    parser.add_argument("db", nargs="?", default="docs.db")
    parser.add_argument("--rn-dir", default=".")
    parser.add_argument("--fail-on-error", action="store_true")
    args = parser.parse_args()
    reindex_release_notes(Path(args.db), Path(args.rn_dir), fail_on_error=args.fail_on_error)


if __name__ == "__main__":
    main()
