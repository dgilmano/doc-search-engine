"""Click CLI entrypoint: doc-search <command>"""
import click

from doc_search_engine.build import build_db_cmd
from doc_search_engine.db import read_build_manifest, validate_database, validate_metadata
from doc_search_engine.index import index_cmd
from doc_search_engine.pdf_index import index_pdfs, reindex_pdfs
from doc_search_engine.rn import index_release_notes, reindex_release_notes


@click.group()
def main():
    """Full-text search engine search tools."""
    pass


main.add_command(index_cmd, name="index")
main.add_command(build_db_cmd, name="build-db")


@main.command("index-rn")
@click.option("--db", "db_path", default="docs.db", show_default=True,
              type=click.Path(dir_okay=False),
              help="SQLite database path.")
@click.option("--rn-dir", default=".", show_default=True,
              type=click.Path(file_okay=False),
              help="Directory containing rn_*.csv and rn_eol.json.")
@click.option("--fail-on-error", is_flag=True,
              help="Exit with an error if any expected RN source is missing or empty.")
def index_rn_cmd(db_path: str, rn_dir: str, fail_on_error: bool):
    """Index release notes CSV/JSON files."""
    from pathlib import Path
    index_release_notes(Path(db_path), Path(rn_dir), fail_on_error=fail_on_error)


@main.command("reindex-rn")
@click.option("--db", "db_path", default="docs.db", show_default=True,
              type=click.Path(exists=True, dir_okay=False),
              help="SQLite database path.")
@click.option("--rn-dir", default=".", show_default=True,
              type=click.Path(file_okay=False),
              help="Directory containing rn_*.csv and rn_eol.json.")
@click.option("--fail-on-error", is_flag=True,
              help="Exit with an error if any expected RN source is missing or empty.")
def reindex_rn_cmd(db_path: str, rn_dir: str, fail_on_error: bool):
    """Remove existing release notes and index them again."""
    from pathlib import Path
    reindex_release_notes(Path(db_path), Path(rn_dir), fail_on_error=fail_on_error)


@main.command("validate-db")
@click.option("--db", "db_path", default="docs.db", show_default=True,
              type=click.Path(exists=True, dir_okay=False),
              help="SQLite database path.")
def validate_db_cmd(db_path: str):
    """Validate a Full-text search search database."""
    import sqlite3
    from pathlib import Path

    conn = sqlite3.connect(Path(db_path))
    try:
        metadata = validate_metadata(conn)
        errors = validate_database(conn)
        manifest = read_build_manifest(conn)
    finally:
        conn.close()

    if errors:
        for error in errors:
            click.echo(f"ERROR: {error}")
        raise click.ClickException(f"Database validation failed with {len(errors)} error(s).")

    click.echo("Database validation OK")
    click.echo(f"Schema version: {metadata['schema_version']}")
    if manifest:
        click.echo(f"Build manifest entries: {len(manifest)}")


@main.command("index-pdf")
@click.option("--db", "db_path", default="docs.db", show_default=True,
              type=click.Path(dir_okay=False),
              help="SQLite database path.")
@click.option("--pdf-dir", required=True,
              type=click.Path(file_okay=False),
              help="Directory containing chassis installation guide PDFs.")
@click.option("--fail-on-error", is_flag=True,
              help="Exit with an error if any PDF fails to parse.")
def index_pdf_cmd(db_path: str, pdf_dir: str, fail_on_error: bool):
    """Index chassis installation guide PDFs."""
    from pathlib import Path
    index_pdfs(Path(db_path), Path(pdf_dir), fail_on_error=fail_on_error)


@main.command("reindex-pdf")
@click.option("--db", "db_path", default="docs.db", show_default=True,
              type=click.Path(exists=True, dir_okay=False),
              help="SQLite database path.")
@click.option("--pdf-dir", required=True,
              type=click.Path(file_okay=False),
              help="Directory containing chassis installation guide PDFs.")
@click.option("--fail-on-error", is_flag=True,
              help="Exit with an error if any PDF fails to parse.")
def reindex_pdf_cmd(db_path: str, pdf_dir: str, fail_on_error: bool):
    """Remove existing installation guide rows and index PDFs again."""
    from pathlib import Path
    reindex_pdfs(Path(db_path), Path(pdf_dir), fail_on_error=fail_on_error)


@main.command("serve")
def serve_cmd():
    """Start the MCP server (reads DOCS_DB env var)."""
    from doc_search_engine.server import mcp
    mcp.run()
