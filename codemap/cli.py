"""Click-based CLI for CodeMap."""

from __future__ import annotations

import sys
from pathlib import Path

import click

from . import __version__
from .core.map_store import MapStore


@click.group()
@click.version_option(version=__version__, prog_name="codemap")
def cli():
    """CodeMap - LLM-friendly codebase indexer.

    Generate structural indexes of codebases to reduce LLM token consumption.
    """
    pass


@cli.command()
@click.argument("path", default=".", type=click.Path(exists=True))
@click.option(
    "--lang",
    "-l",
    multiple=True,
    help="Languages to index (python, typescript, javascript)",
)
@click.option(
    "--exclude",
    "-e",
    multiple=True,
    help="Additional patterns to exclude",
)
def init(path: str, lang: tuple[str, ...], exclude: tuple[str, ...]):
    """Initialize codemap for a directory.

    Scans the directory and creates a .codemap/ folder with structural
    information about all code files, mirroring the project structure.
    """
    from .core.indexer import Indexer

    root = Path(path).resolve()
    click.echo(f"Scanning {root}...")

    try:
        indexer = Indexer(
            root=root,
            languages=list(lang) if lang else None,
            exclude_patterns=list(exclude) if exclude else None,
        )
        result = indexer.index_all()

        click.echo(f"Found {result['total_files']} files")
        click.echo(f"Indexed {result['total_symbols']} symbols")

        if result.get("errors"):
            click.echo(click.style(f"\nWarnings ({len(result['errors'])}):", fg="yellow"))
            for filepath, error in result["errors"][:5]:
                click.echo(f"  - {filepath}: {error}")
            if len(result["errors"]) > 5:
                click.echo(f"  ... and {len(result['errors']) - 5} more")

        click.echo(f"\nSaved to {root / '.codemap/'}")

    except Exception as e:
        click.echo(click.style(f"Error: {e}", fg="red"), err=True)
        sys.exit(1)


@cli.command()
@click.argument("filepath", type=click.Path(), required=False)
@click.option("--all", "update_all", is_flag=True, help="Update all stale files")
def update(filepath: str | None, update_all: bool):
    """Update index for a file or all stale files.

    If --all is specified, reindexes all files that have changed since
    the last index.
    """
    from .core.indexer import Indexer

    try:
        indexer = Indexer.load_existing()

        if update_all:
            result = indexer.update_all_stale()
            click.echo(f"Updated {result['updated']} files")
            if result.get("errors"):
                click.echo(click.style(f"Errors ({len(result['errors'])}):", fg="red"))
                for filepath, error in result["errors"]:
                    click.echo(f"  - {filepath}: {error}")
        elif filepath:
            result = indexer.update_file(filepath)
            if result.get("removed"):
                click.echo(f"Removed {filepath} from index")
            else:
                click.echo(f"Updated {filepath} ({result['symbols_changed']} symbols changed)")
        else:
            click.echo("Please specify a file path or use --all", err=True)
            sys.exit(1)

    except FileNotFoundError as e:
        click.echo(click.style(f"Error: {e}", fg="red"), err=True)
        click.echo("Run 'codemap init' first to create a codemap.")
        sys.exit(1)
    except Exception as e:
        click.echo(click.style(f"Error: {e}", fg="red"), err=True)
        sys.exit(1)


@cli.command()
@click.argument("query")
@click.option("--type", "-t", "symbol_type", help="Filter by type (class, function, method)")
@click.option(
    "--fuzzy", "-f", is_flag=True, help="Enable fuzzy matching (word overlap + similarity)"
)
def find(query: str, symbol_type: str | None, fuzzy: bool):
    """Find a symbol in the codebase.

    Searches for symbols matching the query string (case-insensitive).
    Use --fuzzy for word-level and similarity-based matching.
    """
    from .core.map_store import MapStore

    try:
        store = MapStore.load()
        results = store.find_symbol(query, symbol_type=symbol_type, fuzzy=fuzzy)

        if not results:
            if not fuzzy:
                click.echo(f"No symbols found matching '{query}'")
                click.echo(click.style("Tip: try --fuzzy for broader matching", fg="yellow"))
            else:
                click.echo(f"No symbols found matching '{query}' (even with fuzzy search)")
            return

        for result in results:
            lines = result["lines"]
            click.echo(
                f"{result['file']}:{lines[0]}-{lines[1]} "
                f"[{click.style(result['type'], fg='cyan')}] "
                f"{click.style(result['name'], fg='green')}"
            )
            if result.get("signature"):
                click.echo(f"  {result['signature']}")

    except FileNotFoundError:
        click.echo(click.style("No codemap found. Run 'codemap init' first.", fg="red"), err=True)
        sys.exit(1)
    except Exception as e:
        click.echo(click.style(f"Error: {e}", fg="red"), err=True)
        sys.exit(1)


@cli.command()
@click.argument("filepath")
def show(filepath: str):
    """Show structure of a file.

    Displays all symbols in the file with their line numbers and types.
    """
    from .core.map_store import MapStore

    try:
        store = MapStore.load()
        structure = store.get_file_structure(filepath)

        if not structure:
            click.echo(f"File not indexed: {filepath}")
            click.echo("Run 'codemap update' to index it.")
            return

        click.echo(f"File: {click.style(filepath, fg='blue')} (hash: {structure['hash']})")
        click.echo(f"Lines: {structure['lines']}")
        click.echo(f"Language: {structure['language']}")
        click.echo("\nSymbols:")
        _print_symbols(structure["symbols"], indent=0)

    except FileNotFoundError:
        click.echo(click.style("No codemap found. Run 'codemap init' first.", fg="red"), err=True)
        sys.exit(1)
    except Exception as e:
        click.echo(click.style(f"Error: {e}", fg="red"), err=True)
        sys.exit(1)


def _print_symbols(symbols: list[dict], indent: int = 0):
    """Print symbols with indentation.

    Args:
        symbols: List of symbol dictionaries.
        indent: Current indentation level.
    """
    for sym in symbols:
        prefix = "  " * indent
        lines = sym["lines"]
        type_color = {
            "class": "yellow",
            "function": "green",
            "method": "cyan",
            "async_function": "green",
            "async_method": "cyan",
        }.get(sym["type"], "white")

        click.echo(
            f"{prefix}- {click.style(sym['name'], fg='white', bold=True)} "
            f"[{click.style(sym['type'], fg=type_color)}] "
            f"L{lines[0]}-{lines[1]}"
        )

        if sym.get("signature"):
            click.echo(f"{prefix}  {click.style(sym['signature'], dim=True)}")

        if sym.get("docstring"):
            doc = sym["docstring"]
            if len(doc) > 60:
                doc = doc[:57] + "..."
            click.echo(f"{prefix}  {click.style(f'# {doc}', fg='bright_black')}")

        if sym.get("children"):
            _print_symbols(sym["children"], indent + 1)


@cli.command()
@click.argument("filepath", required=False)
def validate(filepath: str | None):
    """Validate file hashes and report stale entries.

    Checks if indexed files have changed since they were last indexed.
    """
    from .core.indexer import Indexer

    try:
        indexer = Indexer.load_existing()

        if filepath:
            is_valid = indexer.validate_file(filepath)
            if is_valid:
                click.echo(f"{filepath} is up to date")
            else:
                click.echo(click.style(f"{filepath} is stale or not indexed", fg="yellow"))
        else:
            stale = indexer.validate_all()

            if stale:
                click.echo(click.style(f"Stale entries ({len(stale)}):", fg="yellow"))
                for path in stale:
                    click.echo(f"  - {path}")
                click.echo("\nRun 'codemap update --all' to refresh")
            else:
                click.echo(click.style("All entries up to date", fg="green"))

    except FileNotFoundError:
        click.echo(click.style("No codemap found. Run 'codemap init' first.", fg="red"), err=True)
        sys.exit(1)
    except Exception as e:
        click.echo(click.style(f"Error: {e}", fg="red"), err=True)
        sys.exit(1)


@cli.command("install-hooks")
def install_hooks():
    """Install git pre-commit hook.

    Installs a hook that automatically updates the codemap when
    Python/TypeScript/JavaScript files are committed.
    """
    from .hooks.installer import install_pre_commit

    try:
        install_pre_commit()
        click.echo(click.style("Git hooks installed", fg="green"))
    except FileNotFoundError as e:
        click.echo(click.style(f"Error: {e}", fg="red"), err=True)
        sys.exit(1)
    except Exception as e:
        click.echo(click.style(f"Error: {e}", fg="red"), err=True)
        sys.exit(1)


@cli.command()
@click.argument("range_spec")
def lines(range_spec: str):
    """Validate a line range is still valid.

    RANGE_SPEC format: path/to/file.py:45-89

    Checks if the specified line range still contains the same content
    hash as when it was indexed.
    """
    try:
        # Parse range spec
        if ":" not in range_spec:
            click.echo("Invalid format. Use: path/to/file.py:45-89", err=True)
            sys.exit(1)

        filepath, line_range = range_spec.rsplit(":", 1)
        if "-" not in line_range:
            click.echo("Invalid format. Use: path/to/file.py:45-89", err=True)
            sys.exit(1)

        start, end = map(int, line_range.split("-"))

        # Check if file is indexed and valid
        from .core.indexer import Indexer

        indexer = Indexer.load_existing()
        is_valid = indexer.validate_file(filepath)

        if is_valid:
            click.echo(click.style(f"Lines {start}-{end} in {filepath} are valid", fg="green"))
        else:
            click.echo(
                click.style(f"File {filepath} has changed - line range may be stale", fg="yellow")
            )
            click.echo("Run 'codemap update' to refresh the index")

    except FileNotFoundError:
        click.echo(click.style("No codemap found. Run 'codemap init' first.", fg="red"), err=True)
        sys.exit(1)
    except ValueError as e:
        click.echo(click.style(f"Invalid line range: {e}", fg="red"), err=True)
        sys.exit(1)
    except Exception as e:
        click.echo(click.style(f"Error: {e}", fg="red"), err=True)
        sys.exit(1)


@cli.command()
@click.argument("path", default=".", type=click.Path(exists=True))
@click.option(
    "--debounce",
    "-d",
    default=0.5,
    type=float,
    help="Debounce time in seconds (default: 0.5)",
)
@click.option(
    "--quiet",
    "-q",
    is_flag=True,
    help="Only show errors, not updates",
)
def watch(path: str, debounce: float, quiet: bool):
    """Watch directory for changes and update index automatically.

    Monitors the directory for file changes and updates the codemap
    in real-time. Press Ctrl+C to stop watching.

    \b
    Examples:
        codemap watch              # Watch current directory
        codemap watch ./src        # Watch specific directory
        codemap watch -d 1.0       # Use 1 second debounce
    """
    import signal
    from datetime import datetime

    try:
        from .core.watcher import CodeMapWatcher
    except ImportError:
        click.echo(
            click.style(
                "Watch mode requires watchdog. Install with: pip install watchdog",
                fg="red",
            ),
            err=True,
        )
        sys.exit(1)

    root = Path(path).resolve()

    # Check if codemap exists
    if not (root / ".codemap").exists():
        click.echo(click.style("No codemap found. Run 'codemap init' first.", fg="red"), err=True)
        sys.exit(1)

    def on_update(filepath: str, symbols_changed: int) -> None:
        if not quiet:
            timestamp = datetime.now().strftime("%H:%M:%S")
            if symbols_changed > 0:
                click.echo(
                    f"[{timestamp}] "
                    f"{click.style('Updated', fg='green')} {filepath} "
                    f"({symbols_changed} symbols changed)"
                )
            else:
                click.echo(f"[{timestamp}] " f"{click.style('Updated', fg='green')} {filepath}")

    def on_error(filepath: str, error: Exception) -> None:
        timestamp = datetime.now().strftime("%H:%M:%S")
        click.echo(
            f"[{timestamp}] " f"{click.style('Error', fg='red')} {filepath}: {error}",
            err=True,
        )

    try:
        watcher = CodeMapWatcher(
            root=root,
            on_update=on_update,
            on_error=on_error,
            debounce_seconds=debounce,
        )
    except FileNotFoundError as e:
        click.echo(click.style(f"Error: {e}", fg="red"), err=True)
        sys.exit(1)

    # Handle Ctrl+C gracefully
    stop_event = False

    def signal_handler(signum, frame):
        nonlocal stop_event
        stop_event = True

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    click.echo(f"Watching {click.style(str(root), fg='blue')} for changes...")
    click.echo(f"Debounce: {debounce}s")
    click.echo("Press Ctrl+C to stop\n")

    try:
        watcher.start()

        # Keep running until interrupted
        while not stop_event:
            try:
                # Sleep in small intervals to check stop_event
                import time

                time.sleep(0.1)
            except KeyboardInterrupt:
                break

    finally:
        watcher.stop()
        click.echo("\nStopped watching.")


@cli.command()
def stats():
    """Show statistics about the current codemap.

    Displays file counts, symbol counts, and other metadata.
    """
    from .core.map_store import MapStore

    try:
        store = MapStore.load()
        manifest = store.manifest

        click.echo(f"\n{click.style('CodeMap Statistics', fg='blue', bold=True)}")
        click.echo("=" * 40)
        click.echo(f"Root: {manifest.root}")
        click.echo(f"Version: {manifest.version}")
        click.echo(f"Generated: {manifest.generated_at}")
        click.echo(f"Indexed directories: {len(manifest.directories)}")
        click.echo()
        click.echo(
            f"Total files: {click.style(str(manifest.stats.get('total_files', 0)), fg='green')}"
        )
        click.echo(
            f"Total symbols: {click.style(str(manifest.stats.get('total_symbols', 0)), fg='green')}"
        )

        # Count by language
        lang_counts: dict[str, int] = {}
        for rel_path, entry in store.get_all_files():
            lang = entry.language
            lang_counts[lang] = lang_counts.get(lang, 0) + 1

        if lang_counts:
            click.echo("\nFiles by language:")
            for lang, count in sorted(lang_counts.items()):
                click.echo(f"  {lang}: {count}")

        # Count by symbol type
        type_counts: dict[str, int] = {}

        def count_types(symbols):
            for sym in symbols:
                type_counts[sym.type] = type_counts.get(sym.type, 0) + 1
                if sym.children:
                    count_types(sym.children)

        for rel_path, entry in store.get_all_files():
            count_types(entry.symbols)

        if type_counts:
            click.echo("\nSymbols by type:")
            for sym_type, count in sorted(type_counts.items(), key=lambda x: -x[1]):
                click.echo(f"  {sym_type}: {count}")

        # Show directory structure
        if manifest.directories:
            click.echo("\nIndexed directories:")
            for directory in sorted(manifest.directories):
                if directory:
                    click.echo(f"  .codemap/{directory}/")
                else:
                    click.echo("  .codemap/ (root files)")

    except FileNotFoundError:
        click.echo(click.style("No codemap found. Run 'codemap init' first.", fg="red"), err=True)
        sys.exit(1)
    except Exception as e:
        click.echo(click.style(f"Error: {e}", fg="red"), err=True)
        sys.exit(1)


if __name__ == "__main__":
    cli()
