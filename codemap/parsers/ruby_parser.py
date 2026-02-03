"""Ruby parser using tree-sitter with configuration-driven extraction."""

from __future__ import annotations

from typing import Optional

from .base import Symbol
from .treesitter_base import TreeSitterParser, LanguageConfig, NodeMapping


RUBY_CONFIG = LanguageConfig(
    name="ruby",
    extensions=[".rb", ".rake", ".gemspec", ".ru", ".thor"],
    grammar_module="ruby",
    node_mappings={
        "module": NodeMapping(
            symbol_type="module",
            name_child="constant",
            body_child="body_statement",
        ),
        "class": NodeMapping(
            symbol_type="class",
            name_child="constant",
            body_child="body_statement",
        ),
        "method": NodeMapping(
            symbol_type="method",
            name_child="identifier",
            signature_child="method_parameters",
        ),
        "singleton_method": NodeMapping(
            symbol_type="singleton_method",
            name_child="identifier",
            signature_child="method_parameters",
        ),
    },
    container_types=[
        "body_statement",      # Contains methods inside classes/modules
        "singleton_class",     # class << self blocks
    ],
    comment_types=["comment"],
)


class RubyParser(TreeSitterParser):
    """Parser for Ruby files using tree-sitter."""

    config = RUBY_CONFIG

    def _extract_children(self, body_node, source_bytes: bytes) -> list[Symbol]:
        """Extract child symbols from a body node.

        Override to handle singleton_class (class << self) blocks.
        Methods defined inside singleton_class are extracted as singleton_methods.
        """
        children = []
        for child in body_node.children:
            if child.type in self.config.node_mappings:
                symbol = self._extract_symbol(child, source_bytes)
                if symbol:
                    # Convert function to method if inside a class
                    if symbol.type == "function":
                        symbol = Symbol(
                            name=symbol.name,
                            type="method",
                            lines=symbol.lines,
                            signature=symbol.signature,
                            docstring=symbol.docstring,
                            children=symbol.children,
                        )
                    elif symbol.type == "async_function":
                        symbol = Symbol(
                            name=symbol.name,
                            type="async_method",
                            lines=symbol.lines,
                            signature=symbol.signature,
                            docstring=symbol.docstring,
                            children=symbol.children,
                        )
                    children.append(symbol)
            # Handle class << self blocks - extract methods as singleton_methods
            elif child.type == "singleton_class":
                singleton_children = self._extract_singleton_class_methods(child, source_bytes)
                children.extend(singleton_children)
        return children

    def _extract_singleton_class_methods(self, node, source_bytes: bytes) -> list[Symbol]:
        """Extract methods from a singleton_class (class << self) block."""
        methods = []
        # Find the body_statement inside singleton_class
        for child in node.children:
            if child.type == "body_statement":
                for body_child in child.children:
                    if body_child.type == "method":
                        symbol = self._extract_symbol(body_child, source_bytes)
                        if symbol:
                            # Convert method to singleton_method
                            methods.append(Symbol(
                                name=symbol.name,
                                type="singleton_method",
                                lines=symbol.lines,
                                signature=symbol.signature,
                                docstring=symbol.docstring,
                                children=symbol.children,
                            ))
        return methods
