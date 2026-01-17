"""Tests for the CSS parser."""

import pytest
from pathlib import Path

from codemap.parsers.css_parser import CssParser, TREE_SITTER_AVAILABLE


# Skip all tests if tree-sitter-css is not installed
pytestmark = pytest.mark.skipif(
    not TREE_SITTER_AVAILABLE,
    reason="tree-sitter-css not installed"
)


@pytest.fixture
def parser():
    """Create a CSS parser instance."""
    return CssParser()


@pytest.fixture
def sample_css():
    """Load sample CSS fixture."""
    fixture_path = Path(__file__).parent / "fixtures" / "sample_styles.css"
    return fixture_path.read_text()


class TestCssParser:
    """Test suite for CSS parser."""

    def test_parser_creation(self, parser):
        """Test that parser can be created."""
        assert parser is not None
        assert parser.language == "css"
        assert ".css" in parser.extensions

    def test_parse_empty_file(self, parser):
        """Test parsing empty CSS."""
        symbols = parser.parse("")
        assert symbols == []

    def test_parse_class_selector(self, parser):
        """Test parsing class selector."""
        css = ".button { color: red; }"
        symbols = parser.parse(css)

        assert len(symbols) == 1
        assert symbols[0].name == ".button"
        assert symbols[0].type == "class"

    def test_parse_id_selector(self, parser):
        """Test parsing ID selector."""
        css = "#header { background: blue; }"
        symbols = parser.parse(css)

        assert len(symbols) == 1
        assert symbols[0].name == "#header"
        assert symbols[0].type == "id"

    def test_parse_element_selector(self, parser):
        """Test parsing element selector."""
        css = "body { margin: 0; }"
        symbols = parser.parse(css)

        assert len(symbols) == 1
        assert symbols[0].name == "body"
        assert symbols[0].type == "selector"

    def test_parse_pseudo_selector(self, parser):
        """Test parsing pseudo selector."""
        css = ":root { --color: red; }"
        symbols = parser.parse(css)

        assert len(symbols) == 1
        assert symbols[0].name == ":root"
        assert symbols[0].type == "pseudo"

    def test_parse_complex_selector(self, parser):
        """Test parsing complex selector."""
        css = ".nav ul li a { color: blue; }"
        symbols = parser.parse(css)

        assert len(symbols) == 1
        assert symbols[0].name == ".nav ul li a"
        assert symbols[0].type == "class"  # First part determines type

    def test_parse_multiple_selectors(self, parser):
        """Test parsing rule with multiple selectors."""
        css = "h1, h2, h3 { font-weight: bold; }"
        symbols = parser.parse(css)

        assert len(symbols) == 1
        # Takes first selector
        assert symbols[0].name == "h1"

    def test_parse_media_query(self, parser):
        """Test parsing media query."""
        css = """
        @media (max-width: 768px) {
            .container { padding: 10px; }
        }
        """
        symbols = parser.parse(css)

        assert len(symbols) == 1
        assert "@media" in symbols[0].name
        assert "max-width: 768px" in symbols[0].name
        assert symbols[0].type == "media"

    def test_parse_media_query_with_nested_rules(self, parser):
        """Test parsing media query with nested rules."""
        css = """
        @media (min-width: 992px) {
            .sidebar { display: block; }
            .content { width: 70%; }
        }
        """
        symbols = parser.parse(css)

        assert len(symbols) == 1
        assert symbols[0].type == "media"
        assert symbols[0].children is not None
        assert len(symbols[0].children) == 2
        assert symbols[0].children[0].name == ".sidebar"
        assert symbols[0].children[1].name == ".content"

    def test_parse_keyframes(self, parser):
        """Test parsing keyframes animation."""
        css = """
        @keyframes fadeIn {
            from { opacity: 0; }
            to { opacity: 1; }
        }
        """
        symbols = parser.parse(css)

        assert len(symbols) == 1
        assert symbols[0].name == "@keyframes fadeIn"
        assert symbols[0].type == "keyframe"

    def test_parse_line_numbers(self, parser):
        """Test that line numbers are correctly extracted."""
        css = """.first {
    color: red;
}

.second {
    color: blue;
}"""
        symbols = parser.parse(css)

        assert len(symbols) == 2
        assert symbols[0].lines[0] == 1
        assert symbols[0].lines[1] == 3
        assert symbols[1].lines[0] == 5
        assert symbols[1].lines[1] == 7

    def test_parse_signature_with_properties(self, parser):
        """Test that signature shows property summary."""
        css = ".btn { padding: 10px; margin: 5px; border: none; }"
        symbols = parser.parse(css)

        assert len(symbols) == 1
        sig = symbols[0].signature
        assert "padding" in sig
        assert "margin" in sig
        assert "border" in sig

    def test_parse_signature_truncates_many_properties(self, parser):
        """Test that signature truncates when many properties."""
        css = """.card {
            display: flex;
            padding: 20px;
            margin: 10px;
            border: 1px solid #ccc;
            border-radius: 8px;
            background: white;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }"""
        symbols = parser.parse(css)

        assert len(symbols) == 1
        sig = symbols[0].signature
        assert "..." in sig
        assert "properties" in sig

    def test_parse_comment_as_docstring(self, parser):
        """Test that preceding comment becomes docstring."""
        css = """
/* Primary button style */
.btn-primary {
    background: blue;
}"""
        symbols = parser.parse(css)

        assert len(symbols) == 1
        assert symbols[0].docstring == "Primary button style"

    def test_parse_sample_fixture(self, parser, sample_css):
        """Test parsing the sample CSS fixture."""
        symbols = parser.parse(sample_css)

        # Should find multiple rules
        assert len(symbols) > 10

        # Find specific symbols by name
        names = [s.name for s in symbols]
        assert ":root" in names
        assert ".main-header" in names
        assert "#hero" in names
        assert any("@media" in name for name in names)
        assert any("@keyframes" in name for name in names)

    def test_parse_selector_truncation(self, parser):
        """Test that very long selectors are truncated."""
        css = ".very-long-class-name .another-long-class .deeply-nested-element .final-item { color: red; }"
        symbols = parser.parse(css)

        assert len(symbols) == 1
        assert len(symbols[0].name) <= 50

    def test_parse_multiple_rules(self, parser):
        """Test parsing multiple CSS rules."""
        css = """
.first { color: red; }
.second { color: green; }
.third { color: blue; }
"""
        symbols = parser.parse(css)

        assert len(symbols) == 3
        assert symbols[0].name == ".first"
        assert symbols[1].name == ".second"
        assert symbols[2].name == ".third"


class TestCssParserEdgeCases:
    """Test edge cases for CSS parser."""

    def test_empty_rule(self, parser):
        """Test handling of empty rule."""
        css = ".empty {}"
        symbols = parser.parse(css)

        assert len(symbols) == 1
        assert symbols[0].signature is None

    def test_css_variables(self, parser):
        """Test handling of CSS custom properties."""
        css = ":root { --primary: blue; --secondary: red; }"
        symbols = parser.parse(css)

        assert len(symbols) == 1
        assert symbols[0].name == ":root"

    @pytest.mark.skip(reason="tree-sitter-css does not support unicode characters in selectors")
    def test_unicode_in_selector(self, parser):
        """Test handling of unicode in selectors."""
        css = ".日本語 { font-family: sans-serif; }"
        symbols = parser.parse(css)

        assert len(symbols) == 1
        assert "日本語" in symbols[0].name

    def test_multiline_comment(self, parser):
        """Test parsing multiline comment as docstring."""
        css = """
/*
 * This is a
 * multiline comment
 */
.styled { color: red; }
"""
        symbols = parser.parse(css)

        assert len(symbols) == 1
        assert "multiline comment" in symbols[0].docstring

    def test_attribute_selector(self, parser):
        """Test handling of attribute selectors."""
        css = 'input[type="email"] { border-color: blue; }'
        symbols = parser.parse(css)

        assert len(symbols) == 1
        assert 'input[type="email"]' in symbols[0].name

    def test_pseudo_element(self, parser):
        """Test handling of pseudo-elements."""
        css = ".btn::before { content: '→'; }"
        symbols = parser.parse(css)

        assert len(symbols) == 1
        assert "::before" in symbols[0].name

    def test_nested_media_queries(self, parser):
        """Test that nested rules in media queries are extracted."""
        css = """
@media screen and (min-width: 768px) {
    #sidebar { width: 300px; }
    .main-content { margin-left: 320px; }
}
"""
        symbols = parser.parse(css)

        assert len(symbols) == 1
        assert symbols[0].type == "media"
        assert symbols[0].children is not None
        assert len(symbols[0].children) == 2

        child_names = [c.name for c in symbols[0].children]
        assert "#sidebar" in child_names
        assert ".main-content" in child_names

    def test_multiple_keyframes(self, parser):
        """Test parsing multiple keyframes."""
        css = """
@keyframes slideIn { from { left: -100%; } to { left: 0; } }
@keyframes fadeOut { from { opacity: 1; } to { opacity: 0; } }
"""
        symbols = parser.parse(css)

        assert len(symbols) == 2
        assert symbols[0].name == "@keyframes slideIn"
        assert symbols[1].name == "@keyframes fadeOut"

    def test_font_face(self, parser):
        """Test that @font-face is not indexed as rule."""
        css = """
@font-face {
    font-family: 'CustomFont';
    src: url('font.woff2');
}
.text { font-family: 'CustomFont'; }
"""
        symbols = parser.parse(css)

        # Only the .text rule should be indexed
        assert len(symbols) == 1
        assert symbols[0].name == ".text"
