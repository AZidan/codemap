"""Tests for the Markdown parser."""

import pytest

from codemap.parsers.markdown_parser import MarkdownParser


class TestMarkdownParser:
    """Tests for MarkdownParser class."""

    @pytest.fixture
    def parser(self):
        return MarkdownParser()

    def test_parse_h2_headers(self, parser):
        source = '''# Title

## First Section

Content here.

## Second Section

More content.
'''
        symbols = parser.parse(source)

        assert len(symbols) == 2
        assert symbols[0].name == "First Section"
        assert symbols[0].type == "section"
        assert symbols[1].name == "Second Section"
        assert symbols[1].type == "section"

    def test_parse_h3_as_children(self, parser):
        source = '''## Parent Section

### Child One

Content.

### Child Two

More content.

## Another Section
'''
        symbols = parser.parse(source)

        assert len(symbols) == 2
        assert symbols[0].name == "Parent Section"
        assert len(symbols[0].children) == 2
        assert symbols[0].children[0].name == "Child One"
        assert symbols[0].children[0].type == "subsection"
        assert symbols[0].children[1].name == "Child Two"

    def test_parse_h4_as_nested_children(self, parser):
        source = '''## Section

### Subsection

#### Deep Item

Content.

#### Another Deep Item

More.
'''
        symbols = parser.parse(source)

        assert len(symbols) == 1
        section = symbols[0]
        assert section.name == "Section"
        assert len(section.children) == 1

        subsection = section.children[0]
        assert subsection.name == "Subsection"
        assert len(subsection.children) == 2
        assert subsection.children[0].name == "Deep Item"
        assert subsection.children[0].type == "subsubsection"

    def test_line_ranges(self, parser):
        source = '''## Section One

Line 3
Line 4

## Section Two

Line 8
'''
        symbols = parser.parse(source)

        assert symbols[0].lines[0] == 1  # H2 at line 1
        assert symbols[0].lines[1] == 5  # Ends before next H2
        assert symbols[1].lines[0] == 6  # H2 at line 6

    def test_docstring_extraction(self, parser):
        source = '''## API Reference

This section documents the API endpoints.
Use this to integrate with our system.

### Endpoints
'''
        symbols = parser.parse(source)

        assert symbols[0].docstring is not None
        assert "API endpoints" in symbols[0].docstring

    def test_orphan_h3_at_root(self, parser):
        source = '''### Orphan Header

Content without parent H2.
'''
        symbols = parser.parse(source)

        assert len(symbols) == 1
        assert symbols[0].name == "Orphan Header"
        assert symbols[0].type == "subsection"

    def test_parse_fixture_file(self, parser):
        """Test parsing the markdown fixture file."""
        import os
        fixture_path = os.path.join(
            os.path.dirname(__file__), "fixtures", "sample_doc.md"
        )
        with open(fixture_path, "r") as f:
            source = f.read()

        symbols = parser.parse(source, fixture_path)

        # Should find H2 sections
        assert len(symbols) >= 3
        names = [s.name for s in symbols]
        assert "Overview" in names
        assert "API Reference" in names
        assert "Configuration" in names

        # Check nested structure
        api_section = next(s for s in symbols if s.name == "API Reference")
        assert len(api_section.children) >= 2
        child_names = [c.name for c in api_section.children]
        assert "Authentication" in child_names
        assert "Endpoints" in child_names

    def test_supported_extensions(self, parser):
        extensions = parser.supported_extensions()
        assert ".md" in extensions
        assert ".markdown" in extensions
