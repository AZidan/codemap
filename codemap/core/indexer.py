"""Main indexing orchestrator for CodeMap."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Optional

from ..parsers.base import Parser, Symbol
from ..parsers.python_parser import PythonParser
from ..utils.config import Config, load_config
from ..utils.file_utils import count_lines, discover_files, get_language
from .hasher import hash_file
from .map_store import MapStore

logger = logging.getLogger(__name__)


class Indexer:
    """Orchestrates the indexing of a codebase."""

    def __init__(
        self,
        root: Path,
        languages: list[str] | None = None,
        exclude_patterns: list[str] | None = None,
        config: Config | None = None,
    ):
        """Initialize the indexer.

        Args:
            root: Root directory to index.
            languages: Optional list of languages to index.
            exclude_patterns: Optional additional exclude patterns.
            config: Optional Config object.
        """
        self.root = root.resolve()
        self.config = config or load_config(self.root)

        # Override config with explicit parameters
        if languages:
            self.config.languages = list(languages)
        if exclude_patterns:
            self.config.exclude_patterns.extend(exclude_patterns)

        # Use new MapStore that manages .codemap/ directory
        self.map_store = MapStore(self.root)
        self._parsers: dict[str, Parser] = {}
        self._init_parsers()

    def _init_parsers(self) -> None:
        """Initialize language parsers."""
        # Python parser (always available)
        self._parsers["python"] = PythonParser()

        # TypeScript/JavaScript parsers (optional, requires tree-sitter)
        try:
            from ..parsers.typescript_parser import TypeScriptParser
            self._parsers["typescript"] = TypeScriptParser()
        except ImportError:
            logger.debug("TypeScript parser not available (tree-sitter not installed)")

        try:
            from ..parsers.javascript_parser import JavaScriptParser
            self._parsers["javascript"] = JavaScriptParser()
        except ImportError:
            logger.debug("JavaScript parser not available (tree-sitter not installed)")

        # Markdown and YAML parsers (always available)
        from ..parsers.markdown_parser import MarkdownParser
        from ..parsers.yaml_parser import YamlParser

        self._parsers["markdown"] = MarkdownParser()
        self._parsers["yaml"] = YamlParser()

        # Kotlin parser (optional, requires tree-sitter)
        try:
            from ..parsers.kotlin_parser import KotlinParser
            self._parsers["kotlin"] = KotlinParser()
        except ImportError:
            logger.debug("Kotlin parser not available (tree-sitter-kotlin not installed)")

        # Swift parser (optional, requires tree-sitter)
        try:
            from ..parsers.swift_parser import SwiftParser
            self._parsers["swift"] = SwiftParser()
        except ImportError:
            logger.debug("Swift parser not available (tree-sitter-swift not installed)")

        # C parser (optional, requires tree-sitter)
        try:
            from ..parsers.c_parser import CParser
            self._parsers["c"] = CParser()
        except ImportError:
            logger.debug("C parser not available (tree-sitter-c not installed)")

        # C++ parser (optional, requires tree-sitter)
        try:
            from ..parsers.cpp_parser import CppParser
            self._parsers["cpp"] = CppParser()
        except ImportError:
            logger.debug("C++ parser not available (tree-sitter-cpp not installed)")

    @classmethod
    def load_existing(cls, root: Path | None = None) -> "Indexer":
        """Load an existing codemap and create an indexer.

        Args:
            root: Optional root directory. Defaults to current directory.

        Returns:
            Indexer instance with existing codemap loaded.
        """
        if root is None:
            root = Path.cwd()
        root = root.resolve()

        # Check if codemap exists
        codemap_dir = root / MapStore.CODEMAP_DIR
        if not codemap_dir.exists():
            raise FileNotFoundError(f"No codemap found at {codemap_dir}")

        indexer = cls(root)
        indexer.map_store = MapStore.load(root)
        return indexer

    def index_all(self) -> dict:
        """Index all files in the root directory.

        Returns:
            Dictionary with indexing statistics.
        """
        # Clear any existing codemap
        self.map_store.clear()

        # Set metadata
        self.map_store.set_metadata(
            root=str(self.root),
            config=self.config.to_dict(),
        )

        total_files = 0
        total_symbols = 0
        errors = []

        for filepath in discover_files(self.root, self.config):
            try:
                symbols = self._index_file(filepath)
                total_files += 1
                total_symbols += self._count_symbols(symbols)
            except Exception as e:
                logger.warning(f"Failed to index {filepath}: {e}")
                errors.append((str(filepath), str(e)))

        # Update stats and save
        self.map_store.update_stats()
        self.map_store.save()

        return {
            "total_files": total_files,
            "total_symbols": total_symbols,
            "errors": errors,
        }

    def _index_file(self, filepath: Path) -> list[Symbol]:
        """Index a single file.

        Args:
            filepath: Path to the file.

        Returns:
            List of extracted symbols.
        """
        language = get_language(filepath)
        if not language:
            return []

        parser = self._parsers.get(language)
        if not parser:
            logger.debug(f"No parser for language {language}")
            return []

        # Read file content
        try:
            content = filepath.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            # Try with errors='replace' for non-UTF-8 files
            content = filepath.read_text(encoding="utf-8", errors="replace")

        # Parse symbols
        try:
            symbols = parser.parse(content, str(filepath))
        except SyntaxError as e:
            logger.warning(f"Syntax error in {filepath}: {e}")
            symbols = []

        # Get relative path
        try:
            rel_path = str(filepath.relative_to(self.root))
        except ValueError:
            rel_path = str(filepath)

        # Update map store
        self.map_store.update_file(
            rel_path=rel_path,
            hash=hash_file(filepath),
            language=language,
            lines=count_lines(filepath),
            symbols=symbols,
        )

        return symbols

    def _count_symbols(self, symbols: list[Symbol] | None) -> int:
        """Count total symbols including children.

        Args:
            symbols: List of symbols.

        Returns:
            Total count.
        """
        if not symbols:
            return 0
        count = len(symbols)
        for symbol in symbols:
            if symbol.children:
                count += self._count_symbols(symbol.children)
        return count

    def update_file(self, filepath: str | Path) -> dict:
        """Update index for a single file.

        Args:
            filepath: Path to the file to reindex.

        Returns:
            Dictionary with update statistics.
        """
        filepath = Path(filepath).resolve()

        if not filepath.exists():
            # File was deleted, remove from index
            try:
                rel_path = str(filepath.relative_to(self.root))
            except ValueError:
                rel_path = str(filepath)

            removed = self.map_store.remove_file(rel_path)
            self.map_store.update_stats()
            self.map_store.save()

            return {
                "removed": removed,
                "symbols_changed": 0,
            }

        # Re-index the file
        try:
            old_entry = self.map_store.get_file(
                str(filepath.relative_to(self.root))
            )
            old_symbol_count = 0
            if old_entry:
                old_symbol_count = self._count_symbols(old_entry.symbols)

            symbols = self._index_file(filepath)
            new_symbol_count = self._count_symbols(symbols)

            self.map_store.update_stats()
            self.map_store.save()

            return {
                "removed": False,
                "symbols_changed": abs(new_symbol_count - old_symbol_count),
            }
        except Exception as e:
            logger.error(f"Failed to update {filepath}: {e}")
            raise

    def update_all_stale(self) -> dict:
        """Update all stale files.

        Returns:
            Dictionary with update statistics.
        """
        stale_files = self.validate_all()
        updated = 0
        errors = []

        for filepath in stale_files:
            try:
                self.update_file(self.root / filepath)
                updated += 1
            except Exception as e:
                errors.append((filepath, str(e)))

        return {
            "updated": updated,
            "errors": errors,
        }

    def validate_all(self) -> list[str]:
        """Validate all file hashes and find stale entries.

        Returns:
            List of relative paths for stale files.
        """
        stale = []

        for rel_path, entry in self.map_store.get_all_files():
            filepath = self.root / rel_path

            if not filepath.exists():
                # File was deleted
                stale.append(rel_path)
                continue

            try:
                current_hash = hash_file(filepath)
                if current_hash != entry.hash:
                    stale.append(rel_path)
            except Exception as e:
                logger.warning(f"Failed to hash {filepath}: {e}")
                stale.append(rel_path)

        return stale

    def validate_file(self, filepath: str | Path) -> bool:
        """Validate a single file's hash.

        Args:
            filepath: Path to the file.

        Returns:
            True if file is up to date, False if stale or missing.
        """
        filepath = Path(filepath)
        try:
            rel_path = str(filepath.relative_to(self.root))
        except ValueError:
            rel_path = str(filepath)

        entry = self.map_store.get_file(rel_path)
        if not entry:
            return False

        full_path = self.root / rel_path
        if not full_path.exists():
            return False

        try:
            current_hash = hash_file(full_path)
            return current_hash == entry.hash
        except Exception:
            return False
