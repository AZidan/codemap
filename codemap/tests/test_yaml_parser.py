"""Tests for the YAML parser."""

import pytest

from codemap.parsers.yaml_parser import YamlParser


class TestYamlParser:
    """Tests for YamlParser class."""

    @pytest.fixture
    def parser(self):
        return YamlParser()

    def test_parse_simple_keys(self, parser):
        source = '''name: "Test Project"
version: "1.0"
author: "Test Author"
'''
        symbols = parser.parse(source)

        assert len(symbols) == 3
        assert symbols[0].name == "name"
        assert symbols[0].type == "key"
        assert symbols[1].name == "version"
        assert symbols[2].name == "author"

    def test_parse_nested_keys(self, parser):
        source = '''database:
  host: localhost
  port: 5432
  name: mydb
'''
        symbols = parser.parse(source)

        assert len(symbols) == 1
        assert symbols[0].name == "database"
        assert symbols[0].type == "section"
        assert len(symbols[0].children) == 3
        assert symbols[0].children[0].name == "host"
        assert symbols[0].children[1].name == "port"
        assert symbols[0].children[2].name == "name"

    def test_parse_deep_hierarchy(self, parser):
        source = '''config:
  features:
    auth:
      enabled: true
      providers:
        oauth: true
        api_key: false
'''
        symbols = parser.parse(source)

        assert len(symbols) == 1
        config = symbols[0]
        assert config.name == "config"

        features = config.children[0]
        assert features.name == "features"

        auth = features.children[0]
        assert auth.name == "auth"
        assert len(auth.children) >= 2

    def test_parse_list_section(self, parser):
        source = '''screens:
  - id: splash
    title: "Splash"
  - id: login
    title: "Login"
'''
        symbols = parser.parse(source)

        assert len(symbols) == 1
        screens = symbols[0]
        assert screens.name == "screens"
        # List items with keys are captured
        assert len(screens.children) >= 2

    def test_line_ranges(self, parser):
        source = '''first:
  key1: value1
  key2: value2
second:
  key3: value3
'''
        symbols = parser.parse(source)

        assert symbols[0].lines[0] == 1
        assert symbols[0].lines[1] == 3  # Ends before 'second'
        assert symbols[1].lines[0] == 4

    def test_value_preview_as_docstring(self, parser):
        source = '''name: "My Application"
description: "A really long description that goes on and on"
'''
        symbols = parser.parse(source)

        assert symbols[0].docstring == '"My Application"'
        assert symbols[1].docstring is not None

    def test_section_has_no_value_docstring(self, parser):
        source = '''config:
  key: value
'''
        symbols = parser.parse(source)

        # Section markers shouldn't have value previews
        assert symbols[0].docstring is None

    def test_parse_quoted_keys(self, parser):
        source = '''"special-key": value1
'another-key': value2
normal_key: value3
'''
        symbols = parser.parse(source)

        assert len(symbols) == 3
        assert symbols[0].name == "special-key"
        assert symbols[1].name == "another-key"
        assert symbols[2].name == "normal_key"

    def test_skip_comments(self, parser):
        source = '''# This is a comment
name: value
# Another comment
other: value2
'''
        symbols = parser.parse(source)

        assert len(symbols) == 2
        assert symbols[0].name == "name"
        assert symbols[1].name == "other"

    def test_parse_fixture_file(self, parser):
        """Test parsing the YAML fixture file."""
        import os
        fixture_path = os.path.join(
            os.path.dirname(__file__), "fixtures", "sample_config.yaml"
        )
        with open(fixture_path, "r") as f:
            source = f.read()

        symbols = parser.parse(source, fixture_path)

        # Should find root level keys
        names = [s.name for s in symbols]
        assert "version" in names
        assert "product" in names
        assert "features" in names
        assert "design_system" in names

        # Check nested structure
        features = next(s for s in symbols if s.name == "features")
        feature_names = [c.name for c in features.children]
        assert "authentication" in feature_names
        assert "notifications" in feature_names

        # Check deep nesting
        design = next(s for s in symbols if s.name == "design_system")
        design_names = [c.name for c in design.children]
        assert "colors" in design_names
        assert "typography" in design_names

    def test_supported_extensions(self, parser):
        extensions = parser.supported_extensions()
        assert ".yaml" in extensions
        assert ".yml" in extensions
