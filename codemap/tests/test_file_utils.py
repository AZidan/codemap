"""Tests for file utilities module."""

import pytest
from pathlib import Path
from codemap.utils.file_utils import (
    get_language,
    _get_extensions_for_languages,
    is_glob_pattern,
    match_files_to_pattern,
)


class TestLanguageDetection:
    """Test language detection from file extensions."""

    @pytest.mark.parametrize("extension,expected_lang", [
        (".cs", "csharp"),
        (".dart", "dart"),
        (".go", "go"),
        (".java", "java"),
        (".rs", "rust"),
        (".sql", "sql"),
    ])
    def test_get_language_missing_extensions(self, extension, expected_lang):
        """Test that previously missing extensions now map correctly."""
        test_file = Path(f"test{extension}")
        detected = get_language(test_file)
        assert detected == expected_lang

    def test_get_extensions_for_languages_missing(self):
        """Test extension mapping for previously missing languages."""
        languages = ["csharp", "dart", "go", "java", "rust", "sql"]
        extensions = _get_extensions_for_languages(languages)

        expected = [".cs", ".dart", ".go", ".java", ".rs", ".sql"]
        for ext in expected:
            assert ext in extensions, f"{ext} not returned for its language"


class TestGlobPatternDetection:
    """Test glob pattern detection."""

    def test_is_glob_pattern_with_star(self):
        """Test detection of * character."""
        assert is_glob_pattern("*.py") is True
        assert is_glob_pattern("**/*.py") is True
        assert is_glob_pattern("src/*") is True
        assert is_glob_pattern("src/**/*.ts") is True

    def test_is_glob_pattern_with_question(self):
        """Test detection of ? character."""
        assert is_glob_pattern("file?.py") is True
        assert is_glob_pattern("test?.ts") is True

    def test_is_glob_pattern_literal_path(self):
        """Test that literal paths are not detected as globs."""
        assert is_glob_pattern("src/main.py") is False
        assert is_glob_pattern("main.py") is False
        assert is_glob_pattern("path/to/file.ts") is False


class TestMatchFilesToPattern:
    """Test glob pattern matching against file lists."""

    def test_match_simple_extension_pattern(self):
        """Test matching *.ext pattern."""
        files = ["main.py", "utils.py", "main.ts", "README.md"]
        matches = match_files_to_pattern(iter(files), "*.py")
        assert matches == ["main.py", "utils.py"]

    def test_match_recursive_pattern(self):
        """Test matching **/*.ext pattern."""
        files = ["main.py", "src/app.py", "src/components/button.py", "README.md"]
        matches = match_files_to_pattern(iter(files), "**/*.py")
        assert "main.py" in matches
        assert "src/app.py" in matches
        assert "src/components/button.py" in matches
        assert "README.md" not in matches

    def test_match_directory_pattern(self):
        """Test matching src/*.py pattern (fnmatch behavior)."""
        files = ["main.py", "src/app.py", "src/deep/utils.py", "lib/app.py"]
        matches = match_files_to_pattern(iter(files), "src/*.py")
        # Note: fnmatch * matches any characters including /
        assert "src/app.py" in matches
        assert "src/deep/utils.py" in matches
        assert "main.py" not in matches
        assert "lib/app.py" not in matches

    def test_match_no_matches(self):
        """Test when no files match the pattern."""
        files = ["main.py", "utils.py"]
        matches = match_files_to_pattern(iter(files), "*.ts")
        assert matches == []

    def test_match_results_are_sorted(self):
        """Test that results are returned sorted."""
        files = ["z.py", "a.py", "m.py"]
        matches = match_files_to_pattern(iter(files), "*.py")
        assert matches == ["a.py", "m.py", "z.py"]

    def test_match_backslash_normalization(self):
        """Test that Windows-style paths work with Unix-style patterns."""
        files = ["src\\main.py", "src\\utils.py"]
        matches = match_files_to_pattern(iter(files), "src/*.py")
        assert len(matches) == 2

    def test_match_empty_file_list(self):
        """Test matching against empty file list."""
        matches = match_files_to_pattern(iter([]), "*.py")
        assert matches == []
