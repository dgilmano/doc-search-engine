"""Parse Markdown files into article chunks.

Supports standard Markdown format with heading hierarchy.
Each heading becomes a searchable section with its direct content.
"""
from __future__ import annotations

import re
from pathlib import Path

from doc_search_engine.parse import Chunk
from doc_search_engine.products import PRODUCT_PATTERNS


def _detect_product(rel_path: str) -> str:
    """Detect product slug from path parts."""
    parts = Path(rel_path).parts
    for part in parts:
        part_lower = part.lower()
        for pattern, slug in PRODUCT_PATTERNS:
            if pattern.lower() in part_lower:
                return slug
    return parts[0].lower().replace(" ", "-") if parts else "unknown"


def _detect_book(rel_path: str) -> str:
    """Extract book name from path."""
    parts = Path(rel_path).parts
    if len(parts) >= 2:
        for p in parts[:-1]:
            if p not in ("docs", "src", "documentation", "content"):
                return p
        return parts[-2]
    return "unknown"


def _clean(text: str) -> str:
    """Clean up text."""
    text = re.sub(r"[^\S\n]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def _parse_heading_level(line: str) -> int:
    """Extract heading level (1-6)."""
    match = re.match(r"^(#+)", line)
    return len(match.group(1)) if match else 0


def _parse_heading_text(line: str) -> str:
    """Extract heading text."""
    return re.sub(r"^#+\s+", "", line).strip()


def parse_markdown(file_path: Path, docs_root: Path) -> list[Chunk]:
    """Parse Markdown file into chunks.
    
    Each # heading becomes a chunk. Content between headings goes into the
    chunk for that heading. Subheadings create separate chunks.
    """
    try:
        content = file_path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return []

    if not content.strip():
        return []

    rel_path = str(file_path.relative_to(docs_root))
    product_line = _detect_product(rel_path)
    book = _detect_book(rel_path)
    page_title = file_path.stem.replace("-", " ").replace("_", " ").title()

    lines = content.split("\n")
    
    # First pass: identify all headings and their positions
    headings: list[tuple[int, int, int, str]] = []  # (level, line_idx, position, text)
    for i, line in enumerate(lines):
        level = _parse_heading_level(line)
        if level > 0:
            text = _parse_heading_text(line)
            headings.append((level, i, len(headings), text))
    
    if not headings:
        return []
    
    chunks: list[Chunk] = []
    
    # Create chunk for each heading
    for idx, (level, line_idx, _, title) in enumerate(headings):
        # Content is from current heading to next heading of equal/higher priority
        content_start = line_idx + 1
        content_end = len(lines)
        
        # Find next heading at same level or higher (lower number = higher priority)
        for next_level, next_line, _, _ in headings[idx + 1:]:
            if next_line > line_idx:
                if next_level <= level:
                    content_end = next_line
                    break
                # else: deeper heading, keep looking
        
        # Collect content
        content_lines = lines[content_start:content_end]
        # Remove nested headings from content (they'll be in their own chunks)
        filtered_lines = []
        for line in content_lines:
            heading_level = _parse_heading_level(line)
            # Only include if not a heading, or if it's deeper than current level
            if heading_level == 0 or heading_level > level:
                filtered_lines.append(line)
        
        body = _clean("\n".join(filtered_lines))
        
        # Create chunk
        chunk = Chunk(
            product_line=product_line,
            book=book,
            rel_path=rel_path,
            page_title=page_title,
            section_id=f"{rel_path}#{title.lower().replace(' ', '-')}",
            section_title=title,
            section_path=title.lower().replace(" ", "-"),
            depth=level,
            body=body if body else f"({title})",  # Placeholder for empty sections
        )
        chunks.append(chunk)
    
    return chunks
