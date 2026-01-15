"""Kotlin parser using tree-sitter with configuration-driven extraction."""

from __future__ import annotations

from .treesitter_base import TreeSitterParser, LanguageConfig, NodeMapping


def is_kotlin_interface(node) -> bool:
    """Check if a class_declaration is actually an interface."""
    for child in node.children:
        if child.type == "interface":
            return True
    return False


KOTLIN_CONFIG = LanguageConfig(
    name="kotlin",
    extensions=[".kt", ".kts"],
    grammar_module="kotlin",
    node_mappings={
        "class_declaration": NodeMapping(
            symbol_type="class",
            name_child="identifier",
            body_child="class_body",
        ),
        "object_declaration": NodeMapping(
            symbol_type="class",
            name_child="identifier",
            body_child="class_body",
        ),
        "function_declaration": NodeMapping(
            symbol_type="function",
            name_child="identifier",
            signature_child="function_value_parameters",
        ),
    },
    comment_types=["multiline_comment", "line_comment"],
    doc_comment_prefix="/**",
)


class KotlinParser(TreeSitterParser):
    """Parser for Kotlin files using tree-sitter."""

    config = KOTLIN_CONFIG
    extensions = [".kt", ".kts"]
    language = "kotlin"

    def _extract_symbol(self, node, source_bytes):
        """Override to handle interface detection."""
        symbol = super()._extract_symbol(node, source_bytes)
        if symbol and node.type == "class_declaration":
            # Check if it's an interface
            if is_kotlin_interface(node):
                from .base import Symbol
                symbol = Symbol(
                    name=symbol.name,
                    type="interface",
                    lines=symbol.lines,
                    signature=symbol.signature,
                    docstring=symbol.docstring,
                    children=symbol.children,
                )
        return symbol
