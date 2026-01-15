"""JSON map read/write operations for CodeMap with distributed folder structure."""

from __future__ import annotations

import json
import shutil
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterator, Optional

from ..parsers.base import Symbol


@dataclass
class FileEntry:
    """Represents a file entry in the codemap."""

    hash: str
    indexed_at: str
    language: str
    lines: int
    symbols: list[Symbol]

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return {
            "hash": self.hash,
            "indexed_at": self.indexed_at,
            "language": self.language,
            "lines": self.lines,
            "symbols": [s.to_dict() for s in self.symbols],
        }

    @classmethod
    def from_dict(cls, data: dict) -> "FileEntry":
        """Create FileEntry from dictionary."""
        return cls(
            hash=data["hash"],
            indexed_at=data["indexed_at"],
            language=data["language"],
            lines=data["lines"],
            symbols=[Symbol.from_dict(s) for s in data.get("symbols", [])],
        )


@dataclass
class DirectoryMap:
    """Represents the codemap for a single directory."""

    version: str = "1.0"
    generated_at: str = ""
    directory: str = ""  # Relative path from project root ("" for root)
    files: dict[str, FileEntry] = field(default_factory=dict)

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return {
            "version": self.version,
            "generated_at": self.generated_at,
            "directory": self.directory,
            "files": {name: entry.to_dict() for name, entry in self.files.items()},
        }

    @classmethod
    def from_dict(cls, data: dict) -> "DirectoryMap":
        """Create DirectoryMap from dictionary."""
        files = {}
        for name, entry_data in data.get("files", {}).items():
            files[name] = FileEntry.from_dict(entry_data)

        return cls(
            version=data.get("version", "1.0"),
            generated_at=data.get("generated_at", ""),
            directory=data.get("directory", ""),
            files=files,
        )


@dataclass
class RootManifest:
    """The root manifest that tracks all indexed directories."""

    version: str = "1.0"
    generated_at: str = ""
    root: str = ""
    config: dict = field(default_factory=dict)
    stats: dict = field(default_factory=dict)
    directories: list[str] = field(default_factory=list)  # List of indexed directories

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return {
            "version": self.version,
            "generated_at": self.generated_at,
            "root": self.root,
            "config": self.config,
            "stats": self.stats,
            "directories": sorted(self.directories),
        }

    @classmethod
    def from_dict(cls, data: dict) -> "RootManifest":
        """Create RootManifest from dictionary."""
        return cls(
            version=data.get("version", "1.0"),
            generated_at=data.get("generated_at", ""),
            root=data.get("root", ""),
            config=data.get("config", {}),
            stats=data.get("stats", {}),
            directories=data.get("directories", []),
        )


class MapStore:
    """Handles reading and writing distributed codemap files."""

    CODEMAP_DIR = ".codemap"
    MANIFEST_FILE = ".codemap.json"

    def __init__(self, root: Path):
        """Initialize MapStore.

        Args:
            root: Project root directory.
        """
        self.root = root.resolve()
        self.codemap_dir = self.root / self.CODEMAP_DIR
        self._manifest: Optional[RootManifest] = None
        self._dir_maps: dict[str, DirectoryMap] = {}  # Cache for directory maps

    @property
    def manifest(self) -> RootManifest:
        """Get the loaded manifest, loading it if necessary."""
        if self._manifest is None:
            self._manifest = self._load_manifest()
        return self._manifest

    @classmethod
    def load(cls, root: Path | None = None) -> "MapStore":
        """Load an existing codemap from disk.

        Args:
            root: Optional root directory. Defaults to current directory.

        Returns:
            MapStore instance.

        Raises:
            FileNotFoundError: If no codemap exists at the specified location.
        """
        if root is None:
            root = Path.cwd()
        root = root.resolve()

        codemap_dir = root / cls.CODEMAP_DIR
        manifest_path = codemap_dir / cls.MANIFEST_FILE

        if not manifest_path.exists():
            raise FileNotFoundError(f"No codemap found at {codemap_dir}")

        store = cls(root)
        store._manifest = store._load_manifest()
        return store

    def _load_manifest(self) -> RootManifest:
        """Load the root manifest from file.

        Returns:
            RootManifest object, or empty manifest if file doesn't exist.
        """
        manifest_path = self.codemap_dir / self.MANIFEST_FILE
        if not manifest_path.exists():
            return RootManifest()

        try:
            with open(manifest_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            return RootManifest.from_dict(data)
        except (json.JSONDecodeError, KeyError):
            return RootManifest()

    def _get_dir_map_path(self, directory: str) -> Path:
        """Get the path to a directory's codemap file.

        Args:
            directory: Relative directory path ("" for root directory files).

        Returns:
            Path to the .codemap.json file for that directory.
        """
        if directory == "":
            # Root-level files get their own special file
            return self.codemap_dir / "_root.codemap.json"
        return self.codemap_dir / directory / self.MANIFEST_FILE

    def _load_dir_map(self, directory: str) -> DirectoryMap:
        """Load a directory's codemap.

        Args:
            directory: Relative directory path.

        Returns:
            DirectoryMap object.
        """
        if directory in self._dir_maps:
            return self._dir_maps[directory]

        map_path = self._get_dir_map_path(directory)
        if not map_path.exists():
            dir_map = DirectoryMap(directory=directory)
        else:
            try:
                with open(map_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                dir_map = DirectoryMap.from_dict(data)
            except (json.JSONDecodeError, KeyError):
                dir_map = DirectoryMap(directory=directory)

        self._dir_maps[directory] = dir_map
        return dir_map

    def _save_dir_map(self, directory: str) -> None:
        """Save a directory's codemap.

        Args:
            directory: Relative directory path.
        """
        dir_map = self._dir_maps.get(directory)
        if not dir_map:
            return

        dir_map.generated_at = datetime.now(timezone.utc).isoformat()
        map_path = self._get_dir_map_path(directory)

        # Create parent directories
        map_path.parent.mkdir(parents=True, exist_ok=True)

        data = dir_map.to_dict()
        with open(map_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, sort_keys=True)

    def save_manifest(self) -> None:
        """Save the root manifest."""
        self.codemap_dir.mkdir(parents=True, exist_ok=True)
        self.manifest.generated_at = datetime.now(timezone.utc).isoformat()

        manifest_path = self.codemap_dir / self.MANIFEST_FILE
        data = self.manifest.to_dict()
        with open(manifest_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, sort_keys=True)

    def save(self) -> None:
        """Save all modified directory maps and the manifest."""
        # Save all cached directory maps
        for directory in list(self._dir_maps.keys()):
            self._save_dir_map(directory)

        # Save manifest
        self.save_manifest()

    def update_file(
        self,
        rel_path: str,
        hash: str,
        language: str,
        lines: int,
        symbols: list[Symbol],
    ) -> None:
        """Update or add a file entry.

        Args:
            rel_path: Relative path to the file from project root.
            hash: File content hash.
            language: Programming language.
            lines: Number of lines in file.
            symbols: List of extracted symbols.
        """
        # Determine which directory this file belongs to
        path = Path(rel_path)
        directory = str(path.parent) if path.parent != Path(".") else ""
        filename = path.name

        # Load or create the directory map
        dir_map = self._load_dir_map(directory)

        # Add/update the file entry
        dir_map.files[filename] = FileEntry(
            hash=hash,
            indexed_at=datetime.now(timezone.utc).isoformat(),
            language=language,
            lines=lines,
            symbols=symbols,
        )

        # Ensure directory is in the manifest
        if directory not in self.manifest.directories:
            self.manifest.directories.append(directory)

    def remove_file(self, rel_path: str) -> bool:
        """Remove a file entry.

        Args:
            rel_path: Relative path to the file.

        Returns:
            True if file was removed, False if it didn't exist.
        """
        path = Path(rel_path)
        directory = str(path.parent) if path.parent != Path(".") else ""
        filename = path.name

        dir_map = self._load_dir_map(directory)
        if filename in dir_map.files:
            del dir_map.files[filename]

            # If directory is now empty, remove it from manifest and cache
            if not dir_map.files:
                if directory in self.manifest.directories:
                    self.manifest.directories.remove(directory)
                if directory in self._dir_maps:
                    del self._dir_maps[directory]
                # Remove the empty directory's codemap file
                map_path = self._get_dir_map_path(directory)
                if map_path.exists():
                    map_path.unlink()
                    # Try to remove empty parent directories in .codemap
                    try:
                        map_path.parent.rmdir()
                    except OSError:
                        pass  # Directory not empty, that's fine

            return True
        return False

    def get_file(self, rel_path: str) -> Optional[FileEntry]:
        """Get a file entry.

        Args:
            rel_path: Relative path to the file.

        Returns:
            FileEntry or None if not found.
        """
        path = Path(rel_path)
        directory = str(path.parent) if path.parent != Path(".") else ""
        filename = path.name

        dir_map = self._load_dir_map(directory)
        return dir_map.files.get(filename)

    def get_file_hash(self, rel_path: str) -> Optional[str]:
        """Get the hash of a file.

        Args:
            rel_path: Relative path to the file.

        Returns:
            Hash string or None if file not indexed.
        """
        entry = self.get_file(rel_path)
        return entry.hash if entry else None

    def get_file_structure(self, rel_path: str) -> Optional[dict]:
        """Get the structure of a file for display.

        Args:
            rel_path: Relative path to the file.

        Returns:
            Dictionary with file info or None if not found.
        """
        entry = self.get_file(rel_path)
        if not entry:
            return None
        return entry.to_dict()

    def find_symbol(
        self,
        query: str,
        symbol_type: Optional[str] = None,
    ) -> list[dict[str, Any]]:
        """Find symbols matching a query.

        Args:
            query: Symbol name to search for (case-insensitive substring match).
            symbol_type: Optional filter by symbol type.

        Returns:
            List of matching results with file, name, type, and lines.
        """
        results = []
        query_lower = query.lower()

        # Search through all indexed directories
        for directory in self.manifest.directories:
            dir_map = self._load_dir_map(directory)
            for filename, entry in dir_map.files.items():
                # Reconstruct full relative path
                if directory:
                    filepath = f"{directory}/{filename}"
                else:
                    filepath = filename

                for symbol in entry.symbols:
                    results.extend(
                        self._search_symbol(symbol, filepath, query_lower, symbol_type)
                    )

        return results

    def _search_symbol(
        self,
        symbol: Symbol,
        filepath: str,
        query: str,
        symbol_type: Optional[str],
    ) -> Iterator[dict[str, Any]]:
        """Search a symbol and its children.

        Args:
            symbol: Symbol to search.
            filepath: File containing the symbol.
            query: Lowercase query string.
            symbol_type: Optional type filter.

        Yields:
            Matching result dictionaries.
        """
        # Check if symbol matches
        if query in symbol.name.lower():
            if symbol_type is None or symbol.type == symbol_type:
                yield {
                    "file": filepath,
                    "name": symbol.name,
                    "type": symbol.type,
                    "lines": list(symbol.lines),
                    "signature": symbol.signature,
                    "docstring": symbol.docstring,
                }

        # Search children
        for child in symbol.children:
            yield from self._search_symbol(child, filepath, query, symbol_type)

    def update_stats(self) -> None:
        """Update the stats section of the manifest."""
        total_files = 0
        total_symbols = 0

        for directory in self.manifest.directories:
            dir_map = self._load_dir_map(directory)
            total_files += len(dir_map.files)
            for entry in dir_map.files.values():
                total_symbols += self._count_symbols(entry.symbols)

        self.manifest.stats = {
            "total_files": total_files,
            "total_symbols": total_symbols,
            "last_full_index": datetime.now(timezone.utc).isoformat(),
        }

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

    def set_metadata(self, root: str, config: dict) -> None:
        """Set codemap metadata.

        Args:
            root: Absolute path to project root.
            config: Configuration dictionary.
        """
        self.manifest.root = root
        self.manifest.config = config
        self.manifest.generated_at = datetime.now(timezone.utc).isoformat()

    def get_all_files(self) -> Iterator[tuple[str, FileEntry]]:
        """Iterate over all indexed files.

        Yields:
            Tuples of (relative_path, FileEntry).
        """
        for directory in self.manifest.directories:
            dir_map = self._load_dir_map(directory)
            for filename, entry in dir_map.files.items():
                if directory:
                    yield f"{directory}/{filename}", entry
                else:
                    yield filename, entry

    def clear(self) -> None:
        """Remove the entire .codemap directory."""
        if self.codemap_dir.exists():
            shutil.rmtree(self.codemap_dir)
        self._manifest = RootManifest()
        self._dir_maps.clear()


# Legacy compatibility aliases
CodeMap = RootManifest
