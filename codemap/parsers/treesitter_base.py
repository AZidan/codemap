"""Base class for tree-sitter based parsers with configuration-driven extraction."""

from __future__ import annotations

from abc import abstractmethod
from dataclasses import dataclass, field
from typing import Optional, Callable

from .base import Parser, Symbol

# Tree-sitter imports - optional dependency
try:
    from tree_sitter import Language, Parser as TSParser, Node
    TREE_SITTER_AVAILABLE = True
except ImportError:
    TREE_SITTER_AVAILABLE = False
    TSParser = None
    Node = None


@dataclass
class NodeMapping:
    """Configuration for how to extract a symbol from a node type."""

    symbol_type: str  # The symbol type to emit (e.g., "function", "class", "method")
    name_child: str | list[str]  # Child node type(s) containing the name
    signature_child: str | None = None  # Child node type for parameters/signature
    body_child: str | None = None  # Child node type containing children symbols
    docstring_extractor: str = "preceding_comment"  # How to extract docstring
    is_async_check: Callable[["Node"], bool] | None = None  # Check if async


@dataclass
class LanguageConfig:
    """Configuration for a language parser."""

    name: str  # Language name (e.g., "go", "java")
    extensions: list[str]  # File extensions (e.g., [".go"])
    grammar_module: str  # Tree-sitter grammar module name

    # Mapping of tree-sitter node types to symbol extraction config
    node_mappings: dict[str, NodeMapping] = field(default_factory=dict)

    # Node types that contain exportable children (like export_statement)
    export_wrappers: list[str] = field(default_factory=list)

    # Comment node types for docstring extraction
    comment_types: list[str] = field(default_factory=lambda: ["comment"])

    # Node types that wrap declarations but aren't symbols themselves
    # (e.g., namespace_declaration, declaration_list in C#)
    # The parser will recursively traverse into these to find symbols.
    container_types: list[str] = field(default_factory=list)

    # JSDoc-style comment prefix (e.g., "/**" for JS, "///" for C#)
    doc_comment_prefix: str | None = None


class TreeSitterParser(Parser):
    """Base parser using tree-sitter with configuration-driven extraction."""

    config: LanguageConfig  # Subclasses must define this

    def __init__(self):
        if not TREE_SITTER_AVAILABLE:
            raise ImportError(
                f"tree-sitter and tree-sitter-{self.config.name} are required. "
                f"Install with: pip install tree-sitter tree-sitter-{self.config.name}"
            )

        # Dynamically import the grammar module
        import importlib
        grammar = importlib.import_module(f"tree_sitter_{self.config.grammar_module}")
        self._parser = TSParser(Language(grammar.language()))

    @property
    def extensions(self) -> list[str]:
        return self.config.extensions

    @property
    def language(self) -> str:
        return self.config.name

    def parse(self, source: str, filepath: str = "") -> list[Symbol]:
        """Parse source code and extract symbols."""
        source_bytes = source.encode("utf-8")
        tree = self._parser.parse(source_bytes)
        return self._extract_symbols(tree.root_node, source_bytes)

    def _extract_symbols(self, node: "Node", source_bytes: bytes) -> list[Symbol]:
        """Extract symbols from AST node."""
        symbols = []

        for child in node.children:
            # Check if this is a mapped node type
            if child.type in self.config.node_mappings:
                symbol = self._extract_symbol(child, source_bytes)
                if symbol:
                    symbols.append(symbol)

            # Check for export wrappers
            elif child.type in self.config.export_wrappers:
                symbols.extend(self._extract_from_wrapper(child, source_bytes))

            # Recursively traverse container types (e.g., C# namespaces)
            elif child.type in self.config.container_types:
                symbols.extend(self._extract_symbols(child, source_bytes))

        return symbols

    def _extract_symbol(self, node: "Node", source_bytes: bytes) -> Optional[Symbol]:
        """Extract a symbol from a node using the mapping configuration."""
        mapping = self.config.node_mappings.get(node.type)
        if not mapping:
            return None

        # Extract name
        name = self._extract_name(node, mapping, source_bytes)
        if not name:
            return None

        # Determine symbol type (check for async)
        symbol_type = mapping.symbol_type
        if mapping.is_async_check and mapping.is_async_check(node):
            symbol_type = f"async_{symbol_type}"

        # Extract signature
        signature = None
        if mapping.signature_child:
            signature = self._extract_signature(node, mapping, source_bytes)

        # Extract docstring
        docstring = self._extract_docstring(node, source_bytes)

        # Extract children
        children = []
        if mapping.body_child:
            body = self._find_child(node, mapping.body_child)
            if body:
                children = self._extract_children(body, source_bytes)

        return Symbol(
            name=name,
            type=symbol_type,
            lines=(node.start_point[0] + 1, node.end_point[0] + 1),
            signature=signature,
            docstring=docstring,
            children=children if children else None,
        )

    def _extract_name(self, node: "Node", mapping: NodeMapping, source_bytes: bytes) -> str:
        """Extract symbol name from node."""
        name_children = mapping.name_child
        if isinstance(name_children, str):
            name_children = [name_children]

        for child_type in name_children:
            name_node = self._find_child(node, child_type)
            if name_node:
                return self._get_node_text(name_node, source_bytes)

        return "<anonymous>"

    def _extract_signature(self, node: "Node", mapping: NodeMapping, source_bytes: bytes) -> Optional[str]:
        """Extract function/method signature."""
        if not mapping.signature_child:
            return None

        sig_node = self._find_child(node, mapping.signature_child)
        if sig_node:
            sig = self._get_node_text(sig_node, source_bytes)
            # Also try to get return type
            return_node = self._find_child(node, "return_type") or self._find_child(node, "type_annotation")
            if return_node:
                sig += f" : {self._get_node_text(return_node, source_bytes)}"
            return sig
        return None

    def _extract_docstring(self, node: "Node", source_bytes: bytes) -> Optional[str]:
        """Extract docstring from preceding comment."""
        if node.prev_sibling and node.prev_sibling.type in self.config.comment_types:
            comment = self._get_node_text(node.prev_sibling, source_bytes)
            return self._clean_comment(comment)
        return None

    def _clean_comment(self, comment: str) -> Optional[str]:
        """Clean up a comment to extract docstring content."""
        if not comment:
            return None

        # Handle different comment styles
        if comment.startswith("/**"):
            # JSDoc style
            comment = comment[3:-2].strip()
            lines = []
            for line in comment.split("\n"):
                line = line.strip().lstrip("*").strip()
                if line and not line.startswith("@"):
                    lines.append(line)
            return " ".join(lines)[:150] if lines else None
        elif comment.startswith("///"):
            # C#/Rust doc comment
            return comment[3:].strip()[:150]
        elif comment.startswith("//"):
            return comment[2:].strip()[:150]
        elif comment.startswith("#"):
            return comment[1:].strip()[:150]

        return comment.strip()[:150] if comment.strip() else None

    def _extract_children(self, body_node: "Node", source_bytes: bytes) -> list[Symbol]:
        """Extract child symbols from a body node."""
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
        return children

    def _extract_from_wrapper(self, node: "Node", source_bytes: bytes) -> list[Symbol]:
        """Extract symbols from wrapper nodes like export statements."""
        symbols = []
        for child in node.children:
            if child.type in self.config.node_mappings:
                symbol = self._extract_symbol(child, source_bytes)
                if symbol:
                    symbols.append(symbol)
        return symbols

    def _find_child(self, node: "Node", child_type: str) -> Optional["Node"]:
        """Find a child node by type."""
        for child in node.children:
            if child.type == child_type:
                return child
        return None

    def _get_node_text(self, node: Optional["Node"], source_bytes: bytes) -> str:
        """Get the text content of a node."""
        if node is None:
            return ""
        return source_bytes[node.start_byte:node.end_byte].decode("utf-8")
