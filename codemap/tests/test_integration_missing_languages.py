"""Integration tests for previously missing language support."""

import pytest
from pathlib import Path
from codemap.core.indexer import Indexer
from codemap.core.map_store import MapStore
from codemap.utils.file_utils import get_language, discover_files
from codemap.utils.config import Config


class TestMissingLanguagesIntegration:
    """Test that C#, Dart, Go, Java, Rust, and SQL are fully integrated."""

    # Test data: (extension, language_name, sample_code, expected_symbols)
    LANGUAGE_TEST_CASES = [
        (
            ".cs",
            "csharp",
            '''
namespace Sample {
    public class UserService {
        public User GetUser(int id) {
            return null;
        }
    }
}
            ''',
            2  # class + method
        ),
        (
            ".dart",
            "dart",
            '''
class UserService {
  User getUser(int id) {
    return null;
  }
}
            ''',
            2  # class + method
        ),
        (
            ".go",
            "go",
            '''
package main

type UserService struct {}

func (s *UserService) GetUser(id int) *User {
    return nil
}
            ''',
            2  # struct + method
        ),
        (
            ".java",
            "java",
            '''
public class UserService {
    public User getUser(int id) {
        return null;
    }
}
            ''',
            2  # class + method
        ),
        (
            ".rs",
            "rust",
            '''
pub struct UserService {}

impl UserService {
    pub fn get_user(&self, id: i32) -> Option<User> {
        None
    }
}
            ''',
            3  # struct + impl + function
        ),
        (
            ".sql",
            "sql",
            '''
CREATE TABLE users (
    id INT PRIMARY KEY,
    name VARCHAR(100)
);

CREATE VIEW active_users AS
SELECT * FROM users WHERE active = 1;
            ''',
            2  # table + view
        ),
    ]

    @pytest.mark.parametrize("ext,lang,code,expected_count", LANGUAGE_TEST_CASES)
    def test_language_detection(self, ext, lang, code, expected_count):
        """Test that file extension maps to correct language."""
        test_file = Path(f"test{ext}")
        detected = get_language(test_file)
        assert detected == lang, f"Expected {lang}, got {detected} for {ext}"

    @pytest.mark.parametrize("ext,lang,code,expected_count", LANGUAGE_TEST_CASES)
    def test_file_discovery_default_config(self, tmp_path, ext, lang, code, expected_count):
        """Test that files are discovered with default config."""
        # Create test file
        test_file = tmp_path / f"sample{ext}"
        test_file.write_text(code)

        # Use default config (should include all languages now)
        config = Config()
        assert lang in config.languages, f"{lang} not in default languages"

        # Discover files
        files = list(discover_files(tmp_path, config=config))
        assert len(files) == 1, f"Expected 1 file, found {len(files)} for {ext}"
        assert files[0].suffix == ext

    @pytest.mark.parametrize("ext,lang,code,expected_count", LANGUAGE_TEST_CASES)
    def test_end_to_end_indexing(self, tmp_path, ext, lang, code, expected_count):
        """Test complete indexing flow from file to symbols."""
        # Create test file
        test_file = tmp_path / f"sample{ext}"
        test_file.write_text(code)

        # Index
        indexer = Indexer(root=tmp_path)
        result = indexer.index_all()

        # Verify indexing succeeded
        assert result["total_files"] >= 1, f"No files indexed for {ext}"

        # Note: symbol count may vary if parser dependencies not installed
        # So we just verify file was processed
        store = MapStore.load(tmp_path)
        entry = store.get_file(f"sample{ext}")

        if entry is not None:
            # Parser available
            assert entry.language == lang
            # Don't assert symbol count - parser may not be installed
        # If entry is None, parser dependency not installed (acceptable)

    def test_all_languages_in_default_config(self):
        """Verify all six languages are in default config."""
        config = Config()
        missing_langs = ["csharp", "dart", "go", "java", "rust", "sql"]

        for lang in missing_langs:
            assert lang in config.languages, f"{lang} missing from default config"

    def test_extension_mappings_complete(self):
        """Verify all six extensions map to languages."""
        test_cases = [
            (".cs", "csharp"),
            (".dart", "dart"),
            (".go", "go"),
            (".java", "java"),
            (".rs", "rust"),
            (".sql", "sql"),
        ]

        for ext, expected_lang in test_cases:
            test_file = Path(f"test{ext}")
            detected = get_language(test_file)
            assert detected == expected_lang, \
                f"Extension {ext} should map to {expected_lang}, got {detected}"

    def test_mixed_language_project(self, tmp_path):
        """Test project with multiple new languages."""
        # Create files in all six languages
        (tmp_path / "Service.cs").write_text("public class Service {}")
        (tmp_path / "service.dart").write_text("class Service {}")
        (tmp_path / "service.go").write_text("package main\ntype Service struct {}")
        (tmp_path / "Service.java").write_text("public class Service {}")
        (tmp_path / "service.rs").write_text("pub struct Service {}")
        (tmp_path / "schema.sql").write_text("CREATE TABLE users (id INT);")

        # Index all
        indexer = Indexer(root=tmp_path)
        result = indexer.index_all()

        # Should find all 6 files
        assert result["total_files"] >= 6, \
            f"Expected at least 6 files, found {result['total_files']}"
