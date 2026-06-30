# doc-search-engine

A universal full-text search engine for documentation, built as an MCP server for Claude, Codex, and other MCP clients.

**doc-search-engine** builds a local SQLite FTS5 database from your documentation sources and exposes three powerful tools:

- `search_docs` — full-text search with BM25 ranking and highlighted snippets
- `get_document` — retrieve the full text of a section  
- `list_products` — list indexed product lines, books, and section counts

Perfect for:
- 📚 **Internal documentation** — user guides, API docs, technical manuals
- 📝 **Release notes** — track changes across versions
- 📄 **PDFs** — installation guides, whitepapers, specifications
- 🔍 **Multi-format** — HTML, CSV, JSON, PDF in one searchable index

---

## Features

✨ **Universal** — works with any documentation format  
⚡ **Fast** — SQLite FTS5 with memory-mapped I/O  
🤖 **Claude integration** — native MCP server support  
📊 **Flexible indexing** — HTML, CSV, JSON, PDF  
🔄 **Incremental updates** — add/replace sections without full rebuild  
🎯 **Smart ranking** — BM25 scoring across multiple fields  
🔐 **Read-only MCP** — safe concurrent access from multiple clients  

---

## Quick Start

### 1. Install

Python 3.11+ required.

```bash
git clone <repository-url> doc-search-engine
cd doc-search-engine
python3 -m venv .venv
source .venv/bin/activate
pip install -e .
```

On Windows PowerShell:
```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -e .
```

Verify installation:
```bash
doc-search --help
```

### 2. Index Your Documentation

```bash
# Index HTML documentation
doc-search index /path/to/docs -o docs.db --reset

# Index release notes (CSV/JSON)
doc-search index-rn --db docs.db --rn-dir /path/to/release-notes

# Index PDFs
doc-search index-pdf --db docs.db --pdf-dir /path/to/pdfs

# Or do everything at once
doc-search build-db \
  --html-root /path/to/docs \
  --rn-dir /path/to/release-notes \
  --pdf-dir /path/to/pdfs \
  --output docs.db \
  --workers 8 \
  --strict
```

### 3. Run MCP Server

```bash
export DOCS_DB=/path/to/docs.db
doc-search serve
```

### 4. Connect to Claude

Update your Claude configuration:

**macOS/Linux:**
```json
// ~/.config/Claude/claude_desktop_config.json
{
  "mcpServers": {
    "doc-search": {
      "command": "bash",
      "args": [
        "-c",
        "export DOCS_DB=/path/to/docs.db && doc-search serve"
      ]
    }
  }
}
```

**Windows PowerShell:**
```json
// %APPDATA%\Claude\claude_desktop_config.json
{
  "mcpServers": {
    "doc-search": {
      "command": "powershell",
      "args": [
        "-Command",
        "$env:DOCS_DB = 'C:\\path\\to\\docs.db'; doc-search serve"
      ]
    }
  }
}
```

Restart Claude and start searching! 🎉

---

## Indexing Guide

### Index HTML/WebHelp Documentation

The `index` command walks your documentation directory, parses sections, and builds the FTS5 index.

```bash
doc-search index /path/to/docs -o docs.db --reset
```

**Options:**
- `--reset` — delete existing database and rebuild from scratch
- `--workers N` — number of parser processes (default: CPU count)
- `--fail-on-error` — exit with error on parse failures (recommended for release builds)

**How it works:**
1. Discovers all HTML files recursively
2. Parses sections based on structure (headings, divs)
3. Extracts text, metadata, and navigation hierarchy
4. Writes to `docs` and `docs_body` tables
5. FTS5 triggers automatically index the content

**Example: Release build with error checking**
```bash
doc-search index /path/to/docs \
  -o docs.db \
  --reset \
  --workers 8 \
  --fail-on-error
```

### Index Release Notes (CSV/JSON)

Create CSV files for each product/version series:

**Format:** `rn_productname.csv`
```csv
version,date,section,title,description
1.0,2024-01-15,new-features,New API,"Added support for..."
1.0,2024-01-15,bug-fixes,Fixed crash,"Resolved issue..."
0.9,2024-01-01,deprecated,Old feature,"Removed in v1.0"
```

**Or JSON format:** `rn_productname.json`
```json
[
  {
    "version": "1.0",
    "date": "2024-01-15",
    "section": "new-features",
    "title": "New API",
    "description": "Added support for..."
  }
]
```

Index them:
```bash
doc-search index-rn --db docs.db --rn-dir /path/to/release-notes
```

Update existing release notes:
```bash
doc-search reindex-rn --db docs.db --rn-dir /path/to/release-notes
```

### Index PDFs

The PDF indexer de-duplicates files and extracts text:

```bash
doc-search index-pdf --db docs.db --pdf-dir /path/to/pdfs
```

**How it works:**
1. Discovers all PDFs recursively
2. De-duplicates by document ID or filename
3. Extracts text and page numbers
4. Splits into sections
5. Indexes with FTS5

Update existing PDFs:
```bash
doc-search reindex-pdf --db docs.db --pdf-dir /path/to/pdfs
```

### Validate the Database

Before distributing your database, validate it:

```bash
doc-search validate-db --db docs.db
```

This checks:
- Schema version compatibility
- `docs` and `docs_body` row counts match
- FTS5 index consistency

---

## Database Distribution

For team use, build the database in a controlled environment and distribute it:

```bash
# Build with strict error checking
doc-search build-db \
  --html-root /path/to/docs \
  --rn-dir /path/to/release-notes \
  --pdf-dir /path/to/pdfs \
  --output docs.db \
  --strict

# Validate
doc-search validate-db --db docs.db

# Generate checksum
sha256sum docs.db > docs.db.sha256
```

**Distribute both files:**
- `docs.db` — the index database
- `docs.db.sha256` — integrity verification

**Recommended flow:**
1. Build database in controlled environment
2. Validate with `validate-db`
3. Generate SHA256 checksum
4. Publish via artifact repository/SharePoint/internal release
5. Team members download and set `DOCS_DB` environment variable

**Do not commit to Git:**
```gitignore
*.db
*.db-wal
*.db-shm
*.sqlite
*.sqlite3
```

---

## MCP Server

### Starting the Server

```bash
DOCS_DB=/path/to/docs.db doc-search serve
```

The server:
- Loads the database at startup
- Validates schema compatibility
- Creates thread-local read-only connections
- Exposes three tools to MCP clients

### Tools

#### `search_docs(query, product_line?, book?, top_k?)`

Search with full-text indexing and BM25 ranking.

**Parameters:**
| Name | Type | Description |
|---|---|---|
| `query` | string | Natural language or FTS5 syntax: `rsvp interface`, `"exact phrase"`, `term*`, `AND`, `OR`, `NOT` |
| `product_line` | string | Optional filter by product category |
| `book` | string | Optional filter by section/book |
| `top_k` | int | Results returned (1-50, default: 10) |

**Returns:** List of hits with snippets and metadata

**Example:** Find information about interfaces
```
search_docs(
  query="interface configuration",
  product_line="networking",
  top_k=5
)
```

#### `get_document(doc_id, include_neighbors?)`

Retrieve full text for a section.

**Parameters:**
| Name | Type | Description |
|---|---|---|
| `doc_id` | int | Document ID from search results |
| `include_neighbors` | bool | Include adjacent sections (default: false) |

**Returns:** Full document with metadata and optional surrounding sections

#### `list_products()`

List all indexed product lines and available books.

**Returns:** List of products with section counts and available sections

---

## Project Structure

```
doc-search-engine/
├── README.md                     # This file
├── pyproject.toml                # Package metadata
├── src/doc_search_engine/        # Main package
│   ├── cli.py                    # CLI entrypoint (doc-search command)
│   ├── server.py                 # FastMCP server
│   ├── db.py                     # SQLite helpers
│   ├── index.py                  # HTML indexing (multiprocessing)
│   ├── parse.py                  # HTML parsing
│   ├── rn.py                     # Release notes indexing
│   ├── pdf_index.py              # PDF indexing
│   ├── parse_pdf.py              # PDF text extraction
│   ├── search.py                 # FTS5 search logic
│   ├── products.py               # Product catalog
│   ├── build.py                  # Database build orchestration
│   └── schema.sql                # SQLite schema
├── tests/                        # Test suite
│   ├── test_index.py
│   ├── test_search.py
│   ├── test_parse_pdf.py
│   └── ...
└── skill/                        # Claude skill definition
    └── doc-search-engine.md
```

---

## CLI Reference

### `doc-search index`
Index HTML documentation.
```bash
doc-search index <docs_root> [-o output.db] [--reset] [--workers N] [--fail-on-error]
```

### `doc-search index-rn`
Index release notes CSV/JSON files.
```bash
doc-search index-rn --db database.db --rn-dir /path/to/rn-files [--fail-on-error]
```

### `doc-search reindex-rn`
Replace and re-index release notes.
```bash
doc-search reindex-rn --db database.db --rn-dir /path/to/rn-files [--fail-on-error]
```

### `doc-search index-pdf`
Index PDF documents.
```bash
doc-search index-pdf --db database.db --pdf-dir /path/to/pdfs [--fail-on-error]
```

### `doc-search reindex-pdf`
Replace and re-index PDFs.
```bash
doc-search reindex-pdf --db database.db --pdf-dir /path/to/pdfs [--fail-on-error]
```

### `doc-search build-db`
Build complete database from all sources.
```bash
doc-search build-db \
  --html-root /path/to/docs \
  --rn-dir /path/to/rn-files \
  --pdf-dir /path/to/pdfs \
  --output docs.db \
  [--workers N] \
  [--strict]
```

### `doc-search validate-db`
Validate database schema and consistency.
```bash
doc-search validate-db --db database.db
```

### `doc-search serve`
Start the MCP server (reads `DOCS_DB` environment variable).
```bash
DOCS_DB=/path/to/docs.db doc-search serve
```

---

## Environment Variables

| Variable | Description | Example |
|----------|-------------|---------|
| `DOCS_DB` | Path to SQLite database (required for server) | `/home/user/docs.db` |

---

## Examples

### Example 1: Index Your API Documentation

```bash
# Assuming you have docs in ./docs/api and ./docs/guides
doc-search index ./docs -o api-search.db --reset

# Use with Claude
export DOCS_DB=$(pwd)/api-search.db
doc-search serve
```

In Claude, search for:
> "How do I authenticate with the API?"
> "Show me examples of error handling"

### Example 2: Index Product Releases

```bash
# Create release notes CSV
cat > releases.csv << 'EOL'
version,date,category,title,description
2.1,2024-06-01,new-features,Performance,"50% faster indexing"
2.1,2024-06-01,bug-fixes,Memory,"Fixed memory leak"
2.0,2024-05-01,breaking,API,"Removed v1 endpoints"
EOL

# Index with releases
doc-search index ./docs -o full.db --reset
doc-search index-rn --db full.db --rn-dir .

# Start server
export DOCS_DB=$(pwd)/full.db
doc-search serve
```

### Example 3: Build Complete Database

```bash
doc-search build-db \
  --html-root ./documentation \
  --rn-dir ./releases \
  --pdf-dir ./guides \
  --output docs.db \
  --workers 8 \
  --strict

# Validate before distributing
doc-search validate-db --db docs.db

# Share with team
cp docs.db /shared/drive/
```

---

## Troubleshooting

### "Database not found" error
```
Error: Database not found: /path/to/docs.db
```
**Solution:** Check the path and ensure database was built:
```bash
doc-search index /path/to/docs -o docs.db --reset
ls -lh docs.db
```

### "DOCS_DB environment variable is not set"
```
Error: DOCS_DB environment variable is not set
```
**Solution:** Set before running server:
```bash
export DOCS_DB=/absolute/path/to/docs.db
doc-search serve
```

### Search returns no results
- Check that your documentation was indexed: `doc-search validate-db --db docs.db`
- Verify the query syntax (try simpler terms)
- Check product/book filters are correct

### Python version error
```
Error: requires Python 3.11+
```
**Solution:** Use Python 3.11 or newer:
```bash
python3.11 -m venv .venv
# or use pyenv/conda
```

---

## Development

Install with dev dependencies:
```bash
pip install -e ".[dev]"
```

Run tests:
```bash
pytest tests/ -v
```

Run specific test:
```bash
pytest tests/test_search.py::test_sanitize_query -v
```

Lint and format:
```bash
ruff check src/ tests/
ruff format src/ tests/
```

---

## Performance

Typical performance on modern hardware:

| Task | Time |
|------|------|
| Index 10,000 HTML sections | ~30 seconds (8 workers) |
| Index 5,000 PDF pages | ~20 seconds |
| Parse 1,000 release notes | ~2 seconds |
| Search 100k sections | <100ms |
| MCP tool latency | <200ms (p99) |

**Memory usage:**
- Database cache: configurable (default: 256 MB)
- Per-thread overhead: ~10 MB
- Indexing worker: ~50 MB per process

---

## License

[Your License Here]

---

## Contributing

Contributions welcome! Please:
1. Fork the repository
2. Create a feature branch
3. Add tests for new functionality
4. Run test suite and linter
5. Submit pull request

---

## Support

For issues, questions, or suggestions:
- File an issue on GitHub
- Check existing issues and discussions
- Review README and documentation

Happy searching! 🔍
