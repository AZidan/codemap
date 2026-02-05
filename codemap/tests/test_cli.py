"""Tests for the CLI module."""

import json
import os
import pytest
from pathlib import Path
from click.testing import CliRunner

from codemap.cli import cli


class TestCLI:
    """Tests for CLI commands."""

    @pytest.fixture
    def runner(self):
        return CliRunner()

    @pytest.fixture
    def sample_project(self, tmp_path: Path):
        """Create a sample project structure."""
        (tmp_path / "main.py").write_text('''
def main():
    """Main entry point."""
    print("Hello, World!")

class Application:
    """Main application class."""

    def run(self):
        """Run the application."""
        pass

    def stop(self):
        """Stop the application."""
        pass
''')
        (tmp_path / "utils.py").write_text('''
def helper(x: int) -> str:
    """Helper function."""
    return str(x)
''')
        return tmp_path

    def test_init_command(self, runner, sample_project, monkeypatch):
        monkeypatch.chdir(sample_project)
        result = runner.invoke(cli, ["init", "."])

        assert result.exit_code == 0
        assert "Scanning" in result.output
        assert "Indexed" in result.output
        assert (sample_project / ".codemap").exists()

    def test_init_creates_valid_json(self, runner, sample_project, monkeypatch):
        monkeypatch.chdir(sample_project)
        runner.invoke(cli, ["init", "."])

        # Check manifest exists
        manifest_path = sample_project / ".codemap" / ".codemap.json"
        assert manifest_path.exists()

        with open(manifest_path) as f:
            data = json.load(f)

        assert "version" in data
        assert "directories" in data
        assert data["stats"]["total_files"] == 2

    def test_init_creates_directory_structure(self, runner, tmp_path, monkeypatch):
        """Test that init creates mirrored directory structure."""
        (tmp_path / "src").mkdir()
        (tmp_path / "src" / "components").mkdir()
        (tmp_path / "src" / "main.py").write_text("def main(): pass")
        (tmp_path / "src" / "components" / "button.py").write_text("class Button: pass")

        monkeypatch.chdir(tmp_path)
        result = runner.invoke(cli, ["init", "."])

        assert result.exit_code == 0

        # Verify directory structure is mirrored
        codemap_dir = tmp_path / ".codemap"
        assert (codemap_dir / "src" / ".codemap.json").exists()
        assert (codemap_dir / "src" / "components" / ".codemap.json").exists()

    def test_find_command(self, runner, sample_project, monkeypatch):
        monkeypatch.chdir(sample_project)
        runner.invoke(cli, ["init", "."])
        result = runner.invoke(cli, ["find", "Application"])

        assert result.exit_code == 0
        assert "Application" in result.output
        assert "class" in result.output

    def test_find_with_type_filter(self, runner, sample_project, monkeypatch):
        monkeypatch.chdir(sample_project)
        runner.invoke(cli, ["init", "."])
        result = runner.invoke(cli, ["find", "run", "--type", "method"])

        assert result.exit_code == 0
        assert "method" in result.output

    def test_find_no_results(self, runner, sample_project, monkeypatch):
        monkeypatch.chdir(sample_project)
        runner.invoke(cli, ["init", "."])
        result = runner.invoke(cli, ["find", "nonexistent_symbol"])

        assert "No symbols found" in result.output

    def test_show_command(self, runner, sample_project, monkeypatch):
        monkeypatch.chdir(sample_project)
        runner.invoke(cli, ["init", "."])
        result = runner.invoke(cli, ["show", "main.py"])

        assert result.exit_code == 0
        assert "main.py" in result.output
        assert "Application" in result.output
        assert "main" in result.output

    def test_show_not_indexed(self, runner, sample_project, monkeypatch):
        monkeypatch.chdir(sample_project)
        runner.invoke(cli, ["init", "."])
        result = runner.invoke(cli, ["show", "nonexistent.py"])

        assert "not indexed" in result.output

    def test_validate_command_fresh(self, runner, sample_project, monkeypatch):
        monkeypatch.chdir(sample_project)
        runner.invoke(cli, ["init", "."])
        result = runner.invoke(cli, ["validate"])

        assert result.exit_code == 0
        assert "up to date" in result.output

    def test_validate_command_stale(self, runner, sample_project, monkeypatch):
        monkeypatch.chdir(sample_project)
        runner.invoke(cli, ["init", "."])
        # Modify a file
        (sample_project / "main.py").write_text("# modified\ndef new(): pass")
        result = runner.invoke(cli, ["validate"])

        assert "Stale" in result.output
        assert "main.py" in result.output

    def test_update_command(self, runner, sample_project, monkeypatch):
        monkeypatch.chdir(sample_project)
        runner.invoke(cli, ["init", "."])
        # Modify file
        (sample_project / "main.py").write_text('''
def new_function():
    pass
''')
        result = runner.invoke(cli, ["update", "main.py"])

        assert result.exit_code == 0
        assert "Updated" in result.output

    def test_update_all_command(self, runner, sample_project, monkeypatch):
        monkeypatch.chdir(sample_project)
        runner.invoke(cli, ["init", "."])
        # Modify files
        (sample_project / "main.py").write_text("def modified1(): pass")
        (sample_project / "utils.py").write_text("def modified2(): pass")
        result = runner.invoke(cli, ["update", "--all"])

        assert result.exit_code == 0
        assert "Updated 2 files" in result.output

    def test_version_flag(self, runner):
        result = runner.invoke(cli, ["--version"])
        assert result.exit_code == 0
        assert "1.2.0" in result.output

    def test_init_with_language_filter(self, runner, tmp_path, monkeypatch):
        # Create files of different types
        (tmp_path / "script.py").write_text("def py(): pass")
        (tmp_path / "script.js").write_text("function js() {}")

        monkeypatch.chdir(tmp_path)
        result = runner.invoke(cli, ["init", ".", "-l", "python"])

        assert result.exit_code == 0

        # Should only index Python files - check via MapStore
        from codemap.core.map_store import MapStore
        store = MapStore.load(tmp_path)
        files = list(store.get_all_files())

        file_names = [f[0] for f in files]
        assert "script.py" in file_names
        assert "script.js" not in file_names

    def test_lines_command_valid(self, runner, sample_project, monkeypatch):
        monkeypatch.chdir(sample_project)
        runner.invoke(cli, ["init", "."])
        result = runner.invoke(cli, ["lines", "main.py:1-10"])

        assert result.exit_code == 0
        assert "valid" in result.output.lower()

    def test_lines_command_stale(self, runner, sample_project, monkeypatch):
        monkeypatch.chdir(sample_project)
        runner.invoke(cli, ["init", "."])
        (sample_project / "main.py").write_text("# modified")
        result = runner.invoke(cli, ["lines", "main.py:1-10"])

        assert "changed" in result.output.lower() or "stale" in result.output.lower()

    def test_lines_command_invalid_format(self, runner, sample_project, monkeypatch):
        monkeypatch.chdir(sample_project)
        runner.invoke(cli, ["init", "."])
        result = runner.invoke(cli, ["lines", "invalid_format"])

        assert result.exit_code == 1

    def test_no_codemap_error(self, runner, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        result = runner.invoke(cli, ["find", "something"])

        assert result.exit_code == 1
        assert "init" in result.output.lower()

    def test_stats_command(self, runner, sample_project, monkeypatch):
        monkeypatch.chdir(sample_project)
        runner.invoke(cli, ["init", "."])
        result = runner.invoke(cli, ["stats"])

        assert result.exit_code == 0
        assert "Statistics" in result.output
        assert "Total files" in result.output
        assert "Total symbols" in result.output

    def test_stats_shows_directories(self, runner, tmp_path, monkeypatch):
        """Test that stats command shows indexed directories."""
        (tmp_path / "src").mkdir()
        (tmp_path / "src" / "main.py").write_text("def main(): pass")
        (tmp_path / "lib").mkdir()
        (tmp_path / "lib" / "utils.py").write_text("def utils(): pass")

        monkeypatch.chdir(tmp_path)
        runner.invoke(cli, ["init", "."])
        result = runner.invoke(cli, ["stats"])

        assert result.exit_code == 0
        assert "Indexed directories" in result.output
