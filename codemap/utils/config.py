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

    languages: list[str] = field(default_factory=lambda: ["python", "typescript", "javascript", "markdown", "yaml", "kotlin", "swift", "c", "cpp"])
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


def load_config(root: Path) -> Config:
    """Load configuration from .codemaprc file or return defaults.

    Args:
        root: Project root directory.

    Returns:
        Config object.
    """
    config_path = root / ".codemaprc"
    if config_path.exists():
        return _load_yaml_config(config_path)
    return Config()


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
