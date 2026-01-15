"""File discovery and filtering utilities."""

from __future__ import annotations

import fnmatch
from pathlib import Path
from typing import Iterator

from .config import Config, DEFAULT_EXCLUDE_PATTERNS


def discover_files(
    root: Path,
    config: Config | None = None,
    languages: list[str] | None = None,
) -> Iterator[Path]:
    """Discover files to index.

    Args:
        root: Root directory to scan.
        config: Optional Config object with include/exclude patterns.
        languages: Optional list of languages to filter by.

    Yields:
        Path objects for files to index.
    """
    if config is None:
        config = Config()

    # Determine extensions based on languages
    extensions = _get_extensions_for_languages(languages or config.languages)

    for path in root.rglob("*"):
        if not path.is_file():
            continue

        # Check extension
        if not any(path.suffix == ext for ext in extensions):
            continue

        # Get relative path for pattern matching
        try:
            rel_path = path.relative_to(root)
        except ValueError:
            continue

        rel_str = str(rel_path)

        # Check exclude patterns
        if should_exclude(rel_str, config.exclude_patterns):
            continue

        yield path


def should_exclude(filepath: str, patterns: list[str] | None = None) -> bool:
    """Check if a file should be excluded based on patterns.

    Args:
        filepath: Relative file path to check.
        patterns: List of glob patterns to match against.

    Returns:
        True if the file should be excluded.
    """
    if patterns is None:
        patterns = DEFAULT_EXCLUDE_PATTERNS

    for pattern in patterns:
        if fnmatch.fnmatch(filepath, pattern):
            return True
        # Also check if any parent directory matches
        if "**" in pattern:
            # Handle ** patterns
            simple_pattern = pattern.replace("**", "*")
            if fnmatch.fnmatch(filepath, simple_pattern):
                return True
        # Check path components
        parts = filepath.split("/")
        for part in parts:
            # Check if directory name matches common excludes
            if part in ("node_modules", "__pycache__", ".venv", "venv", "dist", "build", ".git"):
                return True
    return False


def _get_extensions_for_languages(languages: list[str]) -> list[str]:
    """Get file extensions for given languages.

    Args:
        languages: List of language names.

    Returns:
        List of file extensions.
    """
    extension_map = {
        "python": [".py", ".pyi"],
        "typescript": [".ts", ".tsx"],
        "javascript": [".js", ".jsx"],
        "markdown": [".md", ".markdown"],
        "yaml": [".yaml", ".yml"],
        "kotlin": [".kt", ".kts"],
        "swift": [".swift"],
        "c": [".c", ".h"],
        "cpp": [".cpp", ".hpp", ".cc", ".hh", ".cxx", ".hxx"],
    }

    extensions = []
    for lang in languages:
        lang_lower = lang.lower()
        if lang_lower in extension_map:
            extensions.extend(extension_map[lang_lower])
    return extensions


def count_lines(filepath: Path) -> int:
    """Count the number of lines in a file.

    Args:
        filepath: Path to the file.

    Returns:
        Number of lines in the file.
    """
    try:
        with open(filepath, "r", encoding="utf-8", errors="replace") as f:
            return sum(1 for _ in f)
    except Exception:
        return 0


def get_language(filepath: Path) -> str | None:
    """Determine the language of a file based on extension.

    Args:
        filepath: Path to the file.

    Returns:
        Language name or None if unknown.
    """
    suffix = filepath.suffix.lower()
    extension_to_lang = {
        ".py": "python",
        ".pyi": "python",
        ".ts": "typescript",
        ".tsx": "typescript",
        ".js": "javascript",
        ".jsx": "javascript",
        ".md": "markdown",
        ".markdown": "markdown",
        ".yaml": "yaml",
        ".yml": "yaml",
        ".kt": "kotlin",
        ".kts": "kotlin",
        ".swift": "swift",
        ".c": "c",
        ".h": "c",  # Default to C for .h files
        ".cpp": "cpp",
        ".hpp": "cpp",
        ".cc": "cpp",
        ".hh": "cpp",
        ".cxx": "cpp",
        ".hxx": "cpp",
    }
    return extension_to_lang.get(suffix)
