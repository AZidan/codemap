"""Configuration management for CodeMap."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

import yaml


# Default patterns
DEFAULT_INCLUDE_PATTERNS = [
    "**/*.py",
    "**/*.ts",
    "**/*.tsx",
    "**/*.js",
    "**/*.jsx",
    "**/*.md",
    "**/*.yaml",
    "**/*.yml",
    "**/*.kt",
    "**/*.kts",
    "**/*.swift",
    "**/*.c",
    "**/*.h",
    "**/*.cpp",
    "**/*.hpp",
    "**/*.cc",
    "**/*.hh",
    "**/*.cxx",
    "**/*.hxx",
    "**/*.html",
    "**/*.htm",
    "**/*.css",
    "**/*.php",
    "**/*.phtml",
    "**/*.cs",      # C#
    "**/*.dart",    # Dart
    "**/*.go",      # Go
    "**/*.java",    # Java
    "**/*.rs",      # Rust
    "**/*.sql",     # SQL
]

DEFAULT_EXCLUDE_PATTERNS = [
    "**/node_modules/**",
    "**/__pycache__/**",
    "**/venv/**",
    "**/.venv/**",
    "**/dist/**",
    "**/build/**",
    "**/*.min.js",
    "**/migrations/**",
    "**/.git/**",
    "**/.tox/**",
    "**/.eggs/**",
    "**/*.egg-info/**",
]


@dataclass
class Config:
    """CodeMap configuration."""

    languages: list[str] = field(default_factory=lambda: ["python", "typescript", "javascript", "markdown", "yaml", "kotlin", "swift", "c", "cpp", "html", "css", "php", "csharp", "dart", "go", "java", "rust", "sql"])
    exclude_patterns: list[str] = field(default_factory=lambda: DEFAULT_EXCLUDE_PATTERNS.copy())
    include_patterns: list[str] = field(default_factory=lambda: DEFAULT_INCLUDE_PATTERNS.copy())
    max_docstring_length: int = 150
    output: str = ".codemap.json"

    def to_dict(self) -> dict:
        """Convert config to dictionary."""
        return {
            "languages": self.languages,
            "exclude_patterns": self.exclude_patterns,
            "include_patterns": self.include_patterns,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Config":
        """Create config from dictionary."""
        return cls(
            languages=data.get("languages", ["python", "typescript", "javascript"]),
            exclude_patterns=data.get("exclude_patterns", DEFAULT_EXCLUDE_PATTERNS.copy()),
            include_patterns=data.get("include_patterns", DEFAULT_INCLUDE_PATTERNS.copy()),
            max_docstring_length=data.get("max_docstring_length", 150),
            output=data.get("output", ".codemap.json"),
        )


def load_config(root: Path, respect_gitignore: bool = True) -> Config:
    """Load configuration from .codemaprc file or return defaults.

    Args:
        root: Project root directory.
        respect_gitignore: Whether to add .gitignore patterns to excludes.

    Returns:
        Config object.
    """
    config_path = root / ".codemaprc"
    if config_path.exists():
        config = _load_yaml_config(config_path)
    else:
        config = Config()

    # Add .gitignore patterns if present
    if respect_gitignore:
        gitignore_patterns = _load_gitignore(root)
        if gitignore_patterns:
            # Merge gitignore patterns with existing excludes (avoid duplicates)
            existing = set(config.exclude_patterns)
            for pattern in gitignore_patterns:
                if pattern not in existing:
                    config.exclude_patterns.append(pattern)

    return config


def _load_gitignore(root: Path) -> list[str]:
    """Load and parse .gitignore file into glob patterns.

    Args:
        root: Project root directory.

    Returns:
        List of glob patterns from .gitignore.
    """
    gitignore_path = root / ".gitignore"
    if not gitignore_path.exists():
        return []

    patterns = []
    try:
        with open(gitignore_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                # Skip empty lines and comments
                if not line or line.startswith("#"):
                    continue
                # Skip negation patterns (we don't support them yet)
                if line.startswith("!"):
                    continue
                # Convert gitignore pattern to glob pattern
                pattern = _gitignore_to_glob(line)
                if pattern:
                    patterns.append(pattern)
    except Exception:
        pass

    return patterns


def _gitignore_to_glob(pattern: str) -> str:
    """Convert a gitignore pattern to a glob pattern.

    Args:
        pattern: Gitignore pattern.

    Returns:
        Glob pattern suitable for should_exclude.
    """
    # Remove trailing spaces
    pattern = pattern.rstrip()

    # Track if this was explicitly a directory pattern
    is_dir_pattern = pattern.endswith("/")
    if is_dir_pattern:
        pattern = pattern[:-1]

    # Handle root-relative patterns (starting with /)
    is_root_relative = pattern.startswith("/")
    if is_root_relative:
        pattern = pattern[1:]

    # If pattern doesn't contain /, it matches anywhere in the tree
    if "/" not in pattern:
        # Known hidden files - should NOT have /** suffix
        hidden_files = {".env", ".gitignore", ".gitattributes", ".editorconfig",
                        ".prettierrc", ".eslintrc", ".npmrc", ".nvmrc", ".dockerignore",
                        ".python-version", ".ruby-version", ".node-version"}
        if pattern in hidden_files:
            return f"**/{pattern}"

        # Check if it's a file pattern (has wildcard or file extension like .log, .pyc)
        # But NOT hidden dirs like .venv, .git (start with . but no extension after)
        has_extension = "." in pattern and not pattern.startswith(".")
        has_wildcard = "*" in pattern

        if has_wildcard or has_extension:
            # File pattern like *.pyc, *.log, file.txt
            return f"**/{pattern}"
        else:
            # Directory pattern like node_modules, __pycache__, .venv, .git
            return f"**/{pattern}/**"

    # Pattern contains / - it's a path pattern
    # Add ** prefix if not root-relative (to match at any depth)
    if not is_root_relative and not pattern.startswith("**/"):
        pattern = f"**/{pattern}"
    elif is_root_relative:
        pattern = f"**/{pattern}"

    # Add /** suffix for directory patterns (no file extension in last component)
    if is_dir_pattern or _looks_like_directory(pattern):
        if not pattern.endswith("/**"):
            pattern = f"{pattern}/**"

    return pattern


def _looks_like_directory(pattern: str) -> bool:
    """Check if a pattern looks like it refers to a directory.

    Args:
        pattern: Glob pattern to check.

    Returns:
        True if pattern appears to be a directory.
    """
    # Get the last path component
    last_part = pattern.rstrip("/").split("/")[-1]

    # If it has a wildcard, it could be file or dir - treat as file
    if "*" in last_part:
        return False

    # Known hidden files (not directories)
    hidden_files = {".env", ".gitignore", ".gitattributes", ".editorconfig",
                    ".prettierrc", ".eslintrc", ".npmrc", ".nvmrc", ".dockerignore"}
    if last_part in hidden_files:
        return False

    # Known hidden directories
    hidden_dirs = {".venv", ".git", ".svn", ".hg", ".tox", ".nox", ".mypy_cache",
                   ".pytest_cache", ".eggs", ".cache", ".npm", ".yarn"}
    if last_part in hidden_dirs:
        return True

    # If it starts with . but has no other . (like .venv, .git) - likely directory
    if last_part.startswith(".") and last_part.count(".") == 1:
        return True

    # If it has no . at all (like build, dist, node_modules) - directory
    if "." not in last_part:
        return True

    return False


def _load_yaml_config(path: Path) -> Config:
    """Load configuration from YAML file.

    Args:
        path: Path to .codemaprc file.

    Returns:
        Config object.
    """
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f) or {}

        return Config(
            languages=data.get("languages", ["python", "typescript", "javascript"]),
            exclude_patterns=data.get("exclude", DEFAULT_EXCLUDE_PATTERNS.copy()),
            include_patterns=data.get("include", DEFAULT_INCLUDE_PATTERNS.copy()),
            max_docstring_length=data.get("max_docstring_length", 150),
            output=data.get("output", ".codemap.json"),
        )
    except Exception:
        return Config()


def save_config(config: Config, root: Path) -> None:
    """Save configuration to .codemaprc file.

    Args:
        config: Config object to save.
        root: Project root directory.
    """
    config_path = root / ".codemaprc"
    data = {
        "languages": config.languages,
        "exclude": config.exclude_patterns,
        "include": config.include_patterns,
        "max_docstring_length": config.max_docstring_length,
        "output": config.output,
    }
    with open(config_path, "w", encoding="utf-8") as f:
        yaml.safe_dump(data, f, default_flow_style=False, sort_keys=False)
