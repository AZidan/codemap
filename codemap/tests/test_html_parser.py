"""Tests for the HTML parser."""

import pytest
from pathlib import Path

from codemap.parsers.html_parser import HtmlParser, TREE_SITTER_AVAILABLE


# Skip all tests if tree-sitter-html is not installed
pytestmark = pytest.mark.skipif(
    not TREE_SITTER_AVAILABLE,
    reason="tree-sitter-html not installed"
)


@pytest.fixture
def parser():
    """Create an HTML parser instance."""
    return HtmlParser()


@pytest.fixture
def sample_html():
    """Load sample HTML fixture."""
    fixture_path = Path(__file__).parent / "fixtures" / "sample_page.html"
    return fixture_path.read_text()


class TestHtmlParser:
    """Test suite for HTML parser."""

    def test_parser_creation(self, parser):
        """Test that parser can be created."""
        assert parser is not None
        assert parser.language == "html"
        assert ".html" in parser.extensions
        assert ".htm" in parser.extensions

    def test_parse_empty_file(self, parser):
        """Test parsing empty HTML."""
        symbols = parser.parse("")
        assert symbols == []

    def test_parse_minimal_html(self, parser):
        """Test parsing minimal HTML document."""
        html = "<html><body></body></html>"
        symbols = parser.parse(html)
        assert symbols == []  # No semantic elements or IDs

    def test_parse_element_with_id(self, parser):
        """Test parsing elements with ID attributes."""
        html = '<div id="main-content">Hello</div>'
        symbols = parser.parse(html)

        assert len(symbols) == 1
        assert symbols[0].name == "#main-content"
        assert symbols[0].type == "id"

    def test_parse_semantic_header(self, parser):
        """Test parsing semantic header element."""
        html = '<header class="site-header">Content</header>'
        symbols = parser.parse(html)

        assert len(symbols) == 1
        assert symbols[0].name == "<header.site-header>"
        assert symbols[0].type == "element"

    def test_parse_semantic_nav(self, parser):
        """Test parsing semantic nav element."""
        html = "<nav><ul><li>Item</li></ul></nav>"
        symbols = parser.parse(html)

        assert len(symbols) == 1
        assert symbols[0].name == "<nav>"
        assert symbols[0].type == "element"

    def test_parse_semantic_main(self, parser):
        """Test parsing semantic main element."""
        html = "<main>Main content here</main>"
        symbols = parser.parse(html)

        assert len(symbols) == 1
        assert symbols[0].name == "<main>"
        assert symbols[0].type == "element"

    def test_parse_semantic_section(self, parser):
        """Test parsing semantic section element."""
        html = '<section id="intro">Introduction</section>'
        symbols = parser.parse(html)

        assert len(symbols) == 1
        assert symbols[0].name == "#intro"  # ID takes precedence
        assert symbols[0].type == "id"

    def test_parse_semantic_article(self, parser):
        """Test parsing semantic article element."""
        html = "<article><h1>Title</h1><p>Content</p></article>"
        symbols = parser.parse(html)

        assert len(symbols) == 1
        assert symbols[0].name == "<article>"
        assert symbols[0].type == "element"

    def test_parse_semantic_aside(self, parser):
        """Test parsing semantic aside element."""
        html = '<aside class="sidebar">Sidebar</aside>'
        symbols = parser.parse(html)

        assert len(symbols) == 1
        assert symbols[0].name == "<aside.sidebar>"
        assert symbols[0].type == "element"

    def test_parse_semantic_footer(self, parser):
        """Test parsing semantic footer element."""
        html = "<footer>Copyright 2025</footer>"
        symbols = parser.parse(html)

        assert len(symbols) == 1
        assert symbols[0].name == "<footer>"
        assert symbols[0].type == "element"

    def test_parse_form_element(self, parser):
        """Test parsing form element."""
        html = '<form id="login-form" action="/login" method="post"></form>'
        symbols = parser.parse(html)

        assert len(symbols) == 1
        assert symbols[0].name == "#login-form"
        assert symbols[0].type == "id"
        assert "action=" in symbols[0].signature
        assert "method=" in symbols[0].signature

    def test_parse_nested_elements(self, parser):
        """Test parsing nested elements with IDs."""
        html = '''
        <header id="header">
            <nav id="nav">
                <div id="logo">Logo</div>
            </nav>
        </header>
        '''
        symbols = parser.parse(html)

        assert len(symbols) == 1
        assert symbols[0].name == "#header"
        assert symbols[0].children is not None
        assert len(symbols[0].children) == 1
        assert symbols[0].children[0].name == "#nav"
        assert symbols[0].children[0].children is not None
        assert len(symbols[0].children[0].children) == 1
        assert symbols[0].children[0].children[0].name == "#logo"

    def test_parse_line_numbers(self, parser):
        """Test that line numbers are correctly extracted."""
        html = '''<html>
<body>
<header id="test">
    Content
</header>
</body>
</html>'''
        symbols = parser.parse(html)

        assert len(symbols) == 1
        assert symbols[0].lines[0] == 3  # Starts on line 3
        assert symbols[0].lines[1] == 5  # Ends on line 5

    def test_parse_signature_with_attributes(self, parser):
        """Test that signature includes key attributes."""
        html = '<input type="email" id="email-field" name="email" placeholder="Enter email">'
        symbols = parser.parse(html)

        assert len(symbols) == 1
        sig = symbols[0].signature
        assert 'id="email-field"' in sig
        assert 'type="email"' in sig
        assert 'name="email"' in sig

    def test_parse_sample_fixture(self, parser, sample_html):
        """Test parsing the sample HTML fixture."""
        symbols = parser.parse(sample_html)

        # Should find top-level elements (nested elements are children of their parents)
        assert len(symbols) >= 4

        # Find specific elements by name
        names = [s.name for s in symbols]
        assert "#site-header" in names
        assert "#content" in names
        assert "#site-footer" in names

        # Verify nested structure - children should be nested, not top-level
        content = next(s for s in symbols if s.name == "#content")
        assert content.children is not None
        child_names = [c.name for c in content.children]
        assert "#hero" in child_names or "#features" in child_names

    def test_non_semantic_elements_ignored(self, parser):
        """Test that regular divs without IDs are ignored."""
        html = '<div class="container"><span>Text</span></div>'
        symbols = parser.parse(html)
        assert symbols == []

    def test_multiple_classes_first_used(self, parser):
        """Test that first class is used in name."""
        html = '<section class="hero primary featured">Content</section>'
        symbols = parser.parse(html)

        assert len(symbols) == 1
        assert symbols[0].name == "<section.hero>"

    def test_doctype_ignored(self, parser):
        """Test that DOCTYPE is ignored."""
        html = '<!DOCTYPE html><html><body></body></html>'
        symbols = parser.parse(html)
        assert symbols == []


class TestHtmlParserEdgeCases:
    """Test edge cases for HTML parser."""

    def test_self_closing_tags(self, parser):
        """Test handling of self-closing tags."""
        html = '<input id="test" />'
        symbols = parser.parse(html)
        # Self-closing input should be parsed
        assert len(symbols) == 1

    def test_malformed_html(self, parser):
        """Test handling of malformed HTML."""
        html = '<div id="unclosed">'
        symbols = parser.parse(html)
        # Tree-sitter should still parse this
        assert len(symbols) == 1

    def test_special_characters_in_id(self, parser):
        """Test handling of special characters in IDs."""
        html = '<div id="my-element_123">Content</div>'
        symbols = parser.parse(html)

        assert len(symbols) == 1
        assert symbols[0].name == "#my-element_123"

    def test_unicode_content(self, parser):
        """Test handling of unicode content."""
        html = '<section id="日本語">日本語テキスト</section>'
        symbols = parser.parse(html)

        assert len(symbols) == 1
        assert symbols[0].name == "#日本語"

    def test_empty_id_attribute(self, parser):
        """Test handling of empty ID attribute."""
        html = '<div id="">Content</div>'
        symbols = parser.parse(html)
        # Empty ID should not be indexed
        assert symbols == []

    def test_deeply_nested_structure(self, parser):
        """Test parsing deeply nested HTML."""
        html = '''
        <main id="main">
            <section id="sec1">
                <article id="art1">
                    <div id="inner">
                        Content
                    </div>
                </article>
            </section>
        </main>
        '''
        symbols = parser.parse(html)

        assert len(symbols) == 1
        assert symbols[0].name == "#main"

        # Navigate to deepest child
        current = symbols[0]
        expected_names = ["#sec1", "#art1", "#inner"]
        for expected in expected_names:
            assert current.children is not None
            assert len(current.children) == 1
            current = current.children[0]
            assert current.name == expected
