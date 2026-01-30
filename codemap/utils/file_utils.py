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

    # Normalize path separators
    filepath = filepath.replace("\\", "/")

    for pattern in patterns:
        # Normalize pattern separators
        pattern = pattern.replace("\\", "/")

        if _match_glob_pattern(filepath, pattern):
            return True

    return False


def _match_glob_pattern(filepath: str, pattern: str) -> bool:
    """Match a filepath against a glob pattern with ** support.

    Args:
        filepath: Relative file path (e.g., 'src/utils/helper.py')
        pattern: Glob pattern (e.g., '**/.venv/**', '**/node_modules/**')

    Returns:
        True if the filepath matches the pattern.
    """
    # Simple fnmatch patterns (no **)
    if "**" not in pattern:
        return fnmatch.fnmatch(filepath, pattern)

    # Handle ** patterns
    # Split pattern into parts
    pattern_parts = pattern.split("/")
    path_parts = filepath.split("/")

    return _match_parts(path_parts, pattern_parts)


def _match_parts(path_parts: list[str], pattern_parts: list[str]) -> bool:
    """Recursively match path parts against pattern parts.

    Args:
        path_parts: List of path components
        pattern_parts: List of pattern components

    Returns:
        True if parts match.
    """
    if not pattern_parts:
        return not path_parts

    if not path_parts:
        # Check if remaining pattern is all ** or empty
        return all(p == "**" for p in pattern_parts)

    pattern_part = pattern_parts[0]

    if pattern_part == "**":
        # ** can match zero or more path components
        # Try matching zero components (skip **)
        if _match_parts(path_parts, pattern_parts[1:]):
            return True
        # Try matching one component and continue with **
        if _match_parts(path_parts[1:], pattern_parts):
            return True
        return False
    else:
        # Regular pattern part - must match current path part
        if fnmatch.fnmatch(path_parts[0], pattern_part):
            return _match_parts(path_parts[1:], pattern_parts[1:])
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
        "html": [".html", ".htm"],
        "css": [".css"],
        "php": [".php", ".phtml"],
        "csharp": [".cs"],
        "dart": [".dart"],
        "go": [".go"],
        "java": [".java"],
        "rust": [".rs"],
        "sql": [".sql"],
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
        ".html": "html",
        ".htm": "html",
        ".css": "css",
        ".php": "php",
        ".phtml": "php",
        ".cs": "csharp",
        ".dart": "dart",
        ".go": "go",
        ".java": "java",
        ".rs": "rust",
        ".sql": "sql",
    }
    return extension_to_lang.get(suffix)
