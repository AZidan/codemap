"""HTML parser for indexing elements with IDs and semantic elements."""

from __future__ import annotations

from typing import Optional

from .base import Parser, Symbol

# Tree-sitter imports - optional dependency
try:
    from tree_sitter import Language, Parser as TSParser
    import tree_sitter_html as ts_html

    TREE_SITTER_AVAILABLE = True
except ImportError:
    TREE_SITTER_AVAILABLE = False


# Semantic HTML5 elements that are worth indexing
SEMANTIC_ELEMENTS = {
    "header",
    "nav",
    "main",
    "section",
    "article",
    "aside",
    "footer",
    "form",
}


class HtmlParser(Parser):
    """Parser for HTML files - indexes elements with IDs and semantic elements."""

    extensions = [".html", ".htm"]
    language = "html"

    def __init__(self):
        if not TREE_SITTER_AVAILABLE:
            raise ImportError(
                "tree-sitter and tree-sitter-html are required. "
                "Install with: pip install tree-sitter tree-sitter-html"
            )
        self._parser = TSParser(Language(ts_html.language()))

    def parse(self, source: str, filepath: str = "") -> list[Symbol]:
        """Parse HTML source and extract symbols.

        Args:
            source: The HTML source code
            filepath: Optional path to the file being parsed

        Returns:
            List of Symbol objects representing HTML elements
        """
        source_bytes = source.encode("utf-8")
        tree = self._parser.parse(source_bytes)
        return self._extract_symbols(tree.root_node, source_bytes)

    def _extract_symbols(self, node, source_bytes: bytes) -> list[Symbol]:
        """Extract symbols from AST node recursively."""
        symbols = []

        for child in node.children:
            if child.type == "element":
                result = self._process_element(child, source_bytes)
                symbols.extend(result)
            elif child.type == "doctype":
                # Skip doctype
                continue
            else:
                # Recurse into other nodes
                symbols.extend(self._extract_symbols(child, source_bytes))

        return symbols

    def _process_element(self, node, source_bytes: bytes) -> list[Symbol]:
        """Process an element node and return symbols (either the element or its children)."""
        symbol = self._extract_element(node, source_bytes)
        if symbol:
            return [symbol]

        # Element not indexed, but check for indexed children
        children = []
        for child in node.children:
            if child.type == "element":
                children.extend(self._process_element(child, source_bytes))
        return children

    def _extract_element(self, node, source_bytes: bytes) -> Optional[Symbol]:
        """Extract a symbol from an HTML element."""
        # Find the start tag or self-closing tag
        start_tag = None
        for child in node.children:
            if child.type in ("start_tag", "self_closing_tag"):
                start_tag = child
                break

        if not start_tag:
            return None

        # Get tag name
        tag_name = None
        for child in start_tag.children:
            if child.type == "tag_name":
                tag_name = self._get_node_text(child, source_bytes)
                break

        if not tag_name:
            return None

        # Get attributes
        attrs = self._get_attributes(start_tag, source_bytes)
        element_id = attrs.get("id")
        element_class = attrs.get("class")

        # Extract nested elements first
        children = self._extract_nested_elements(node, source_bytes)

        # Determine if this element should be indexed
        should_index = False
        symbol_type = "element"
        name = tag_name

        if element_id:
            # Elements with IDs are always indexed
            should_index = True
            symbol_type = "id"
            name = f"#{element_id}"
        elif tag_name.lower() in SEMANTIC_ELEMENTS:
            # Semantic elements are indexed
            should_index = True
            symbol_type = "element"
            name = f"<{tag_name}>"
            if element_class:
                name = f"<{tag_name}.{element_class.split()[0]}>"

        if should_index:
            return Symbol(
                name=name,
                type=symbol_type,
                lines=(node.start_point[0] + 1, node.end_point[0] + 1),
                signature=self._build_signature(tag_name, attrs),
                docstring=None,
                children=children if children else None,
            )

        # Even if not indexed, we might have indexed children
        if children:
            # Return children at this level if parent not indexed
            return None  # Children will be collected by parent

        return None

    def _extract_nested_elements(self, node, source_bytes: bytes) -> list[Symbol]:
        """Extract nested indexable elements."""
        children = []
        for child in node.children:
            if child.type == "element":
                # Check if this element should be indexed
                symbol = self._extract_element(child, source_bytes)
                if symbol:
                    children.append(symbol)
                else:
                    # Recurse to find deeper indexed elements
                    children.extend(self._extract_nested_elements(child, source_bytes))
        return children

    def _get_attributes(self, start_tag, source_bytes: bytes) -> dict[str, str]:
        """Extract attributes from a start tag."""
        attrs = {}
        for child in start_tag.children:
            if child.type == "attribute":
                attr_name = None
                attr_value = None
                for attr_child in child.children:
                    if attr_child.type == "attribute_name":
                        attr_name = self._get_node_text(attr_child, source_bytes)
                    elif attr_child.type == "attribute_value":
                        attr_value = self._get_node_text(attr_child, source_bytes)
                    elif attr_child.type == "quoted_attribute_value":
                        # Get the actual value inside quotes
                        for qchild in attr_child.children:
                            if qchild.type == "attribute_value":
                                attr_value = self._get_node_text(qchild, source_bytes)
                                break
                if attr_name:
                    attrs[attr_name] = attr_value or ""
        return attrs

    def _build_signature(self, tag_name: str, attrs: dict[str, str]) -> Optional[str]:
        """Build a signature showing key attributes."""
        parts = [f"<{tag_name}"]

        # Include id and class in signature
        if "id" in attrs:
            parts.append(f'id="{attrs["id"]}"')
        if "class" in attrs:
            parts.append(f'class="{attrs["class"]}"')

        # Include other useful attributes
        for attr in ["name", "type", "href", "src", "action", "method"]:
            if attr in attrs and attr not in ("id", "class"):
                value = attrs[attr]
                if len(value) > 30:
                    value = value[:27] + "..."
                parts.append(f'{attr}="{value}"')

        sig = " ".join(parts) + ">"
        return sig if len(sig) <= 100 else sig[:97] + "..."

    def _get_node_text(self, node, source_bytes: bytes) -> str:
        """Get the text content of a node."""
        if node is None:
            return ""
        return source_bytes[node.start_byte:node.end_byte].decode("utf-8")

    @staticmethod
    def supported_extensions() -> list[str]:
        """Return list of supported file extensions."""
        return [".html", ".htm"]
