"""SQL parser using tree-sitter with configuration-driven extraction."""

from __future__ import annotations

from typing import Optional

from .treesitter_base import TreeSitterParser, LanguageConfig, NodeMapping
from .base import Symbol

# Tree-sitter imports - optional dependency
try:
    from tree_sitter import Language, Parser as TSParser, Node
    TREE_SITTER_AVAILABLE = True
except ImportError:
    TREE_SITTER_AVAILABLE = False
    TSParser = None
    Node = None


# Define SQL language configuration
SQL_CONFIG = LanguageConfig(
    name="sql",
    extensions=[".sql"],
    grammar_module="sql",
    node_mappings={
        # Table definitions
        "create_table": NodeMapping(
            symbol_type="table",
            name_child="object_reference",  # Contains identifier
            body_child="column_definitions",
        ),
        # View definitions
        "create_view": NodeMapping(
            symbol_type="view",
            name_child="object_reference",
        ),
        # Materialized view definitions
        "create_materialized_view": NodeMapping(
            symbol_type="materialized_view",
            name_child="object_reference",
        ),
        # Index definitions
        "create_index": NodeMapping(
            symbol_type="index",
            name_child="identifier",  # Direct child
        ),
        # Function definitions
        "create_function": NodeMapping(
            symbol_type="function",
            name_child="object_reference",
            signature_child="function_arguments",
            body_child="function_body",
        ),
        # Trigger definitions
        "create_trigger": NodeMapping(
            symbol_type="trigger",
            name_child="object_reference",
        ),
        # Type definitions (enums, composites, etc.)
        "create_type": NodeMapping(
            symbol_type="type",
            name_child="object_reference",
        ),
        # Sequence definitions
        "create_sequence": NodeMapping(
            symbol_type="sequence",
            name_child="object_reference",
        ),
        # Schema definitions
        "create_schema": NodeMapping(
            symbol_type="schema",
            name_child="identifier",  # Direct child
        ),
        # Database definitions
        "create_database": NodeMapping(
            symbol_type="database",
            name_child="identifier",  # Direct child
        ),
        # Column definitions (for table children)
        "column_definition": NodeMapping(
            symbol_type="column",
            name_child="identifier",
        ),
    },
    comment_types=["comment", "marginalia"],
)


class SQLParser(TreeSitterParser):
    """Parser for SQL files using tree-sitter.

    Extracts:
    - Tables (CREATE TABLE)
    - Views (CREATE VIEW, CREATE MATERIALIZED VIEW)
    - Indexes (CREATE INDEX)
    - Functions (CREATE FUNCTION)
    - Triggers (CREATE TRIGGER)
    - Types (CREATE TYPE)
    - Sequences (CREATE SEQUENCE)
    - Schemas (CREATE SCHEMA)
    - Databases (CREATE DATABASE)
    """

    config = SQL_CONFIG
    extensions = [".sql"]  # Required class attribute
    language = "sql"  # Required class attribute

    def _extract_symbols(self, node: "Node", source_bytes: bytes) -> list[Symbol]:
        """Extract symbols from AST node.

        Override to handle SQL's nested statement structure where
        CREATE statements are wrapped in 'statement' nodes.
        """
        symbols = []

        for child in node.children:
            # Handle direct mappings (e.g., create_table)
            if child.type in self.config.node_mappings:
                symbol = self._extract_symbol(child, source_bytes)
                if symbol:
                    symbols.append(symbol)
            # Handle statement wrappers (SQL-specific)
            elif child.type == "statement":
                # Extract from inside statement wrapper
                for stmt_child in child.children:
                    if stmt_child.type in self.config.node_mappings:
                        symbol = self._extract_symbol(stmt_child, source_bytes)
                        if symbol:
                            symbols.append(symbol)

        return symbols

    def _extract_name(self, node: "Node", mapping: NodeMapping, source_bytes: bytes) -> str:
        """Extract symbol name from node.

        Override to handle SQL's object_reference -> identifier pattern.
        """
        name_children = mapping.name_child
        if isinstance(name_children, str):
            name_children = [name_children]

        for child_type in name_children:
            name_node = self._find_child(node, child_type)
            if name_node:
                # If this is an object_reference, get the identifier inside it
                if name_node.type == "object_reference":
                    identifier = self._find_child(name_node, "identifier")
                    if identifier:
                        return self._get_node_text(identifier, source_bytes)
                return self._get_node_text(name_node, source_bytes)

        return "<anonymous>"

    def _extract_children(self, body_node: "Node", source_bytes: bytes) -> list[Symbol]:
        """Extract child symbols from a body node.

        Override to handle column_definitions structure where columns
        are direct children of the body node.
        """
        children = []
        for child in body_node.children:
            if child.type in self.config.node_mappings:
                symbol = self._extract_symbol(child, source_bytes)
                if symbol:
                    children.append(symbol)
        return children

    def _extract_signature(self, node: "Node", mapping: NodeMapping, source_bytes: bytes) -> Optional[str]:
        """Extract function signature.

        Override to extract parameter types from function_arguments.
        """
        if not mapping.signature_child:
            return None

        sig_node = self._find_child(node, mapping.signature_child)
        if sig_node:
            sig_text = self._get_node_text(sig_node, source_bytes)

            # Try to get return type
            returns_node = self._find_child(node, "keyword_returns")
            if returns_node:
                # Find the type node after RETURNS keyword
                found_returns = False
                for child in node.children:
                    if found_returns and child.type not in ("keyword_returns",):
                        # This should be the return type
                        if child.type == "int":
                            sig_text += " -> INT"
                        elif child.type in ("varchar", "char", "text"):
                            sig_text += f" -> {self._get_node_text(child, source_bytes).upper()}"
                        elif child.type == "identifier":
                            sig_text += f" -> {self._get_node_text(child, source_bytes)}"
                        break
                    if child.type == "keyword_returns":
                        found_returns = True

            return sig_text if sig_text != "()" else None
        return None
