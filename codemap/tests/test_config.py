"""Tests for configuration module."""

import pytest
from pathlib import Path
from codemap.utils.config import Config, DEFAULT_INCLUDE_PATTERNS


class TestConfig:
    """Test configuration defaults and loading."""

    def test_default_languages_include_all(self):
        """Verify all supported languages are in defaults."""
        config = Config()
        expected_languages = [
            "python", "typescript", "javascript", "markdown", "yaml",
            "kotlin", "swift", "c", "cpp", "html", "css", "php",
            "csharp", "dart", "go", "java", "rust", "sql"
        ]

        for lang in expected_languages:
            assert lang in config.languages, f"{lang} missing from default config"

    def test_default_include_patterns_complete(self):
        """Verify all language extensions in default patterns."""
        expected_patterns = [
            "**/*.cs",    # C#
            "**/*.dart",  # Dart
            "**/*.go",    # Go
            "**/*.java",  # Java
            "**/*.rs",    # Rust
            "**/*.sql",   # SQL
        ]

        for pattern in expected_patterns:
            assert pattern in DEFAULT_INCLUDE_PATTERNS, \
                f"{pattern} missing from DEFAULT_INCLUDE_PATTERNS"
