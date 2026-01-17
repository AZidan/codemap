"""CSS parser for indexing selectors, keyframes, and media queries."""

from __future__ import annotations

from typing import Optional

from .base import Parser, Symbol

# Tree-sitter imports - optional dependency
try:
    from tree_sitter import Language, Parser as TSParser
    import tree_sitter_css as ts_css

    TREE_SITTER_AVAILABLE = True
except ImportError:
    TREE_SITTER_AVAILABLE = False


class CssParser(Parser):
    """Parser for CSS files - indexes selectors, keyframes, and media queries."""

    extensions = [".css"]
    language = "css"

    def __init__(self):
        if not TREE_SITTER_AVAILABLE:
            raise ImportError(
                "tree-sitter and tree-sitter-css are required. "
                "Install with: pip install tree-sitter tree-sitter-css"
            )
        self._parser = TSParser(Language(ts_css.language()))

    def parse(self, source: str, filepath: str = "") -> list[Symbol]:
        """Parse CSS source and extract symbols.

        Args:
            source: The CSS source code
            filepath: Optional path to the file being parsed

        Returns:
            List of Symbol objects representing CSS rules
        """
        source_bytes = source.encode("utf-8")
        tree = self._parser.parse(source_bytes)
        return self._extract_symbols(tree.root_node, source_bytes)

    def _extract_symbols(self, node, source_bytes: bytes) -> list[Symbol]:
        """Extract symbols from AST node."""
        symbols = []

        for child in node.children:
            if child.type == "rule_set":
                symbol = self._extract_rule_set(child, source_bytes)
                if symbol:
                    symbols.append(symbol)
            elif child.type == "media_statement":
                symbol = self._extract_media_query(child, source_bytes)
                if symbol:
                    symbols.append(symbol)
            elif child.type == "keyframes_statement":
                symbol = self._extract_keyframes(child, source_bytes)
                if symbol:
                    symbols.append(symbol)
            elif child.type == "import_statement":
                symbol = self._extract_import(child, source_bytes)
                if symbol:
                    symbols.append(symbol)

        return symbols

    def _extract_rule_set(self, node, source_bytes: bytes) -> Optional[Symbol]:
        """Extract a symbol from a CSS rule set."""
        # Get selectors
        selectors_node = None
        for child in node.children:
            if child.type == "selectors":
                selectors_node = child
                break

        if not selectors_node:
            return None

        selector_text = self._get_node_text(selectors_node, source_bytes).strip()
        if not selector_text:
            return None

        # Determine symbol type based on selector
        symbol_type = self._get_selector_type(selector_text)

        # Get a clean name for the symbol
        name = self._get_selector_name(selector_text)

        # Extract properties as signature
        signature = self._extract_properties_summary(node, source_bytes)

        return Symbol(
            name=name,
            type=symbol_type,
            lines=(node.start_point[0] + 1, node.end_point[0] + 1),
            signature=signature,
            docstring=self._get_preceding_comment(node, source_bytes),
            children=None,
        )

    def _extract_media_query(self, node, source_bytes: bytes) -> Optional[Symbol]:
        """Extract a symbol from a media query."""
        # Get the media query condition
        query_text = ""
        children_symbols = []

        for child in node.children:
            if child.type == "feature_query":
                query_text = self._get_node_text(child, source_bytes)
            elif child.type == "block":
                # Extract nested rules
                children_symbols = self._extract_nested_rules(child, source_bytes)

        if not query_text:
            query_text = "all"

        return Symbol(
            name=f"@media {query_text}",
            type="media",
            lines=(node.start_point[0] + 1, node.end_point[0] + 1),
            signature=None,
            docstring=self._get_preceding_comment(node, source_bytes),
            children=children_symbols if children_symbols else None,
        )

    def _extract_keyframes(self, node, source_bytes: bytes) -> Optional[Symbol]:
        """Extract a symbol from a keyframes definition."""
        name = None
        for child in node.children:
            if child.type == "keyframes_name":
                name = self._get_node_text(child, source_bytes)
                break

        if not name:
            return None

        return Symbol(
            name=f"@keyframes {name}",
            type="keyframe",
            lines=(node.start_point[0] + 1, node.end_point[0] + 1),
            signature=None,
            docstring=self._get_preceding_comment(node, source_bytes),
            children=None,
        )

    def _extract_import(self, node, source_bytes: bytes) -> Optional[Symbol]:
        """Extract a symbol from an import statement."""
        import_text = self._get_node_text(node, source_bytes).strip()
        # Extract the URL/path from @import
        if "url(" in import_text:
            start = import_text.find("url(") + 4
            end = import_text.find(")", start)
            path = import_text[start:end].strip("'\"")
        elif '"' in import_text or "'" in import_text:
            # @import "file.css"
            import_text = import_text.replace("@import", "").strip().rstrip(";")
            path = import_text.strip("'\"")
        else:
            path = import_text

        return Symbol(
            name=f"@import {path}",
            type="import",
            lines=(node.start_point[0] + 1, node.end_point[0] + 1),
            signature=None,
            docstring=None,
            children=None,
        )

    def _extract_nested_rules(self, block_node, source_bytes: bytes) -> list[Symbol]:
        """Extract nested rules from a block (e.g., inside @media)."""
        symbols = []
        for child in block_node.children:
            if child.type == "rule_set":
                symbol = self._extract_rule_set(child, source_bytes)
                if symbol:
                    symbols.append(symbol)
        return symbols

    def _get_selector_type(self, selector: str) -> str:
        """Determine the type of CSS selector."""
        selector = selector.strip()

        # Check for ID selector
        if selector.startswith("#"):
            return "id"

        # Check for class selector
        if selector.startswith("."):
            return "class"

        # Check for pseudo-class on root
        if selector.startswith(":"):
            return "pseudo"

        # Element selector or complex selector
        return "selector"

    def _get_selector_name(self, selector: str) -> str:
        """Get a clean name from a selector."""
        selector = selector.strip()

        # Handle multiple selectors (comma-separated)
        if "," in selector:
            # Take first selector
            selector = selector.split(",")[0].strip()

        # Truncate very long selectors
        if len(selector) > 50:
            selector = selector[:47] + "..."

        return selector

    def _extract_properties_summary(self, node, source_bytes: bytes) -> Optional[str]:
        """Extract a summary of CSS properties."""
        # Find the block
        block = None
        for child in node.children:
            if child.type == "block":
                block = child
                break

        if not block:
            return None

        # Count declarations
        declarations = []
        for child in block.children:
            if child.type == "declaration":
                # Get property name
                for dec_child in child.children:
                    if dec_child.type == "property_name":
                        prop_name = self._get_node_text(dec_child, source_bytes)
                        declarations.append(prop_name)
                        break

        if not declarations:
            return None

        # Show first few properties
        if len(declarations) <= 3:
            return f"{{{', '.join(declarations)}}}"
        else:
            return f"{{{', '.join(declarations[:3])}, ...}} ({len(declarations)} properties)"

    def _get_preceding_comment(self, node, source_bytes: bytes) -> Optional[str]:
        """Get preceding comment as docstring."""
        if node.prev_sibling and node.prev_sibling.type == "comment":
            comment = self._get_node_text(node.prev_sibling, source_bytes)
            # Clean up CSS comment
            if comment.startswith("/*") and comment.endswith("*/"):
                comment = comment[2:-2].strip()
                # Remove leading asterisks from multi-line comments
                lines = []
                for line in comment.split("\n"):
                    line = line.strip().lstrip("*").strip()
                    if line:
                        lines.append(line)
                return " ".join(lines)[:150] if lines else None
        return None

    def _get_node_text(self, node, source_bytes: bytes) -> str:
        """Get the text content of a node."""
        if node is None:
            return ""
        return source_bytes[node.start_byte:node.end_byte].decode("utf-8")

    @staticmethod
    def supported_extensions() -> list[str]:
        """Return list of supported file extensions."""
        return [".css"]
