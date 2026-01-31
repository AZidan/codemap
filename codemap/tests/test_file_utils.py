"""Tests for file utilities module."""

import pytest
from pathlib import Path
from codemap.utils.file_utils import get_language, _get_extensions_for_languages


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
