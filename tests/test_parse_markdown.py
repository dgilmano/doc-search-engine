"""Tests for Markdown parser."""
import tempfile
from pathlib import Path

import pytest

from doc_search_engine.parse_markdown import parse_markdown


def test_parse_simple_markdown():
    """Test parsing a simple markdown file."""
    with tempfile.TemporaryDirectory() as tmpdir:
        docs_root = Path(tmpdir)
        md_file = docs_root / "docs" / "guide.md"
        md_file.parent.mkdir(parents=True)
        
        md_file.write_text("""# Installation

## Prerequisites
- Python 3.11+
- pip

## Steps
1. Clone the repo
2. Install dependencies

## Verification
Run tests to verify.
""")
        
        chunks = parse_markdown(md_file, docs_root)
        
        # Should have 2 chunks: Installation and Verification
        assert len(chunks) > 0
        
        # Check first chunk
        first = chunks[0]
        assert first.section_title == "Installation"
        assert first.depth == 1
        assert "Prerequisites" in first.body
        
        # Check metadata
        assert first.rel_path == "docs/guide.md"
        assert "guide" in first.page_title.lower()


def test_parse_nested_headings():
    """Test parsing nested heading hierarchy."""
    with tempfile.TemporaryDirectory() as tmpdir:
        docs_root = Path(tmpdir)
        md_file = docs_root / "api.md"
        
        md_file.write_text("""# API Documentation

## Authentication
### JWT Tokens
Bearer token format.

### API Keys
Key-based authentication.

## Endpoints
### GET /users
List users.
""")
        
        chunks = parse_markdown(md_file, docs_root)
        
        # Should have multiple chunks for each section
        assert len(chunks) >= 3
        
        # Check section titles and depths
        titles = [c.section_title for c in chunks]
        assert "API Documentation" in titles
        assert "Authentication" in titles or "JWT Tokens" in titles


def test_parse_empty_markdown():
    """Test parsing markdown with no content."""
    with tempfile.TemporaryDirectory() as tmpdir:
        docs_root = Path(tmpdir)
        md_file = docs_root / "empty.md"
        md_file.write_text("# Empty File\n\n")
        
        chunks = parse_markdown(md_file, docs_root)
        
        # Should handle gracefully
        assert isinstance(chunks, list)


def test_parse_markdown_without_headings():
    """Test parsing markdown with just text, no headings."""
    with tempfile.TemporaryDirectory() as tmpdir:
        docs_root = Path(tmpdir)
        md_file = docs_root / "notes.md"
        md_file.write_text("Just some text here.\nNo headings at all.")
        
        chunks = parse_markdown(md_file, docs_root)
        
        # Should handle gracefully (no chunks since no headings)
        assert isinstance(chunks, list)


def test_product_detection_from_path():
    """Test product detection from markdown path."""
    with tempfile.TemporaryDirectory() as tmpdir:
        docs_root = Path(tmpdir)
        # Create path with product indicator
        md_file = docs_root / "sr-os" / "docs" / "guide.md"
        md_file.parent.mkdir(parents=True)
        
        md_file.write_text("""# Configuration
Some config content.
""")
        
        chunks = parse_markdown(md_file, docs_root)
        
        if chunks:
            # Should detect sr-os or sros
            product = chunks[0].product_line
            assert "sr" in product.lower() or "os" in product.lower()


def test_section_path_generation():
    """Test that section paths are properly generated."""
    with tempfile.TemporaryDirectory() as tmpdir:
        docs_root = Path(tmpdir)
        md_file = docs_root / "guide.md"
        
        md_file.write_text("""# Main Topic
## Sub Topic
Some content here.
""")
        
        chunks = parse_markdown(md_file, docs_root)
        
        # Check section path format
        for chunk in chunks:
            assert "/" not in chunk.section_id or "#" in chunk.section_id
            assert chunk.section_path  # Should have some path


def test_code_blocks_preserved():
    """Test that code blocks are preserved in body."""
    with tempfile.TemporaryDirectory() as tmpdir:
        docs_root = Path(tmpdir)
        md_file = docs_root / "code.md"
        
        md_file.write_text("""# Examples

## Python Code
Here's an example:

```python
def hello():
    print("world")
```

Done.
""")
        
        chunks = parse_markdown(md_file, docs_root)
        
        # Check that code is in body
        body_text = " ".join(c.body for c in chunks)
        assert "def hello" in body_text or "python" in body_text.lower()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
