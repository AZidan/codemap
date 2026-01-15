"""Swift parser using tree-sitter with configuration-driven extraction."""

from __future__ import annotations

from .treesitter_base import TreeSitterParser, LanguageConfig, NodeMapping


def get_swift_class_type(node) -> str:
    """Determine if a class_declaration is a class, struct, or enum."""
    for child in node.children:
        if child.type == "enum":
            return "enum"
        if child.type == "struct":
            return "class"  # Treat structs as classes
        if child.type == "class":
            return "class"
    return "class"


SWIFT_CONFIG = LanguageConfig(
    name="swift",
    extensions=[".swift"],
    grammar_module="swift",
    node_mappings={
        "class_declaration": NodeMapping(
            symbol_type="class",
            name_child="type_identifier",
            body_child=["class_body", "enum_class_body"],
        ),
        "protocol_declaration": NodeMapping(
            symbol_type="interface",
            name_child="type_identifier",
            body_child="protocol_body",
        ),
        "function_declaration": NodeMapping(
            symbol_type="function",
            name_child="simple_identifier",
        ),
        "protocol_function_declaration": NodeMapping(
            symbol_type="function",
            name_child="simple_identifier",
        ),
    },
    comment_types=["multiline_comment", "comment"],
    doc_comment_prefix="///",
)


class SwiftParser(TreeSitterParser):
    """Parser for Swift files using tree-sitter."""

    config = SWIFT_CONFIG
    extensions = [".swift"]
    language = "swift"

    def _extract_symbol(self, node, source_bytes):
        """Override to handle enum detection and body type variations."""
        # Handle class_declaration which can be struct, class, or enum
        if node.type == "class_declaration":
            symbol_type = get_swift_class_type(node)

            # Find the name
            name = ""
            for child in node.children:
                if child.type == "type_identifier":
                    name = source_bytes[child.start_byte:child.end_byte].decode("utf-8")
                    break

            if not name:
                return None

            # Extract docstring
            docstring = self._extract_docstring(node, source_bytes)

            # Find children from body
            children = []
            for child in node.children:
                if child.type in ["class_body", "enum_class_body"]:
                    children = self._extract_children(child, source_bytes)
                    break

            from .base import Symbol
            return Symbol(
                name=name,
                type=symbol_type,
                lines=(node.start_point[0] + 1, node.end_point[0] + 1),
                signature=None,
                docstring=docstring,
                children=children if children else None,
            )

        return super()._extract_symbol(node, source_bytes)
