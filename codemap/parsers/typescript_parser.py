"""TypeScript parser using tree-sitter."""

from __future__ import annotations

from typing import Optional

from .base import Parser, Symbol

# Tree-sitter imports - optional dependency
try:
    import tree_sitter_typescript as tsts
    from tree_sitter import Language, Parser as TSParser, Node

    TREE_SITTER_AVAILABLE = True
except ImportError:
    TREE_SITTER_AVAILABLE = False
    TSParser = None
    Node = None


class TypeScriptParser(Parser):
    """Parser for TypeScript files using tree-sitter."""

    extensions = [".ts", ".tsx"]
    language = "typescript"

    def __init__(self):
        """Initialize the TypeScript parser."""
        if not TREE_SITTER_AVAILABLE:
            raise ImportError(
                "tree-sitter and tree-sitter-typescript are required. "
                "Install with: pip install tree-sitter tree-sitter-typescript"
            )
        # Use TypeScript language for .ts files, TSX for .tsx
        self._ts_parser = TSParser(Language(tsts.language_typescript()))
        self._tsx_parser = TSParser(Language(tsts.language_tsx()))

    def parse(self, source: str, filepath: str = "") -> list[Symbol]:
        """Parse TypeScript source code and extract symbols.

        Args:
            source: TypeScript source code.
            filepath: Optional file path for determining TSX vs TS.

        Returns:
            List of top-level Symbol objects.
        """
        # Choose parser based on file extension
        parser = self._tsx_parser if filepath.endswith(".tsx") else self._ts_parser

        # Convert to bytes for tree-sitter (it uses byte offsets)
        source_bytes = source.encode("utf-8")
        tree = parser.parse(source_bytes)
        return self._extract_symbols(tree.root_node, source_bytes)

    # Node types that contain symbols but aren't symbols themselves.
    _container_types = {"ambient_declaration", "internal_module", "module", "statement_block"}

    def _extract_symbols(self, node: "Node", source_bytes: bytes) -> list[Symbol]:
        """Extract symbols from tree-sitter AST.

        Args:
            node: Tree-sitter node.
            source_bytes: Original source code as bytes.

        Returns:
            List of Symbol objects.
        """
        symbols = []

        for child in node.children:
            parsed = self._parse_node(child, source_bytes)
            if parsed:
                symbols.extend(parsed) if isinstance(parsed, list) else symbols.append(parsed)
            elif child.type == "export_statement":
                exported = self._parse_export(child, source_bytes)
                if exported:
                    symbols.extend(exported)
            elif child.type in self._container_types:
                # Recurse into ambient declarations, namespaces, modules
                symbols.extend(self._extract_symbols(child, source_bytes))

        return symbols

    def _parse_node(self, node: "Node", source_bytes: bytes) -> Optional[Symbol]:
        """Parse a single node into a Symbol.

        Args:
            node: Tree-sitter node.
            source_bytes: Original source code as bytes.

        Returns:
            Symbol or None if not a recognized symbol type.
        """
        if node.type in ("class_declaration", "abstract_class_declaration"):
            return self._parse_class(node, source_bytes)
        elif node.type in ("function_declaration", "function_signature"):
            return self._parse_function(node, source_bytes, "function")
        elif node.type in ("lexical_declaration", "variable_declaration"):
            return self._parse_lexical_declaration(node, source_bytes)
        elif node.type == "interface_declaration":
            return self._parse_interface(node, source_bytes)
        elif node.type == "type_alias_declaration":
            return self._parse_type_alias(node, source_bytes)
        elif node.type == "enum_declaration":
            return self._parse_enum(node, source_bytes)
        return None

    def _parse_export(self, node: "Node", source_bytes: bytes) -> list[Symbol]:
        """Parse an export statement.

        Args:
            node: Export statement node.
            source_bytes: Original source code as bytes.

        Returns:
            List of exported symbols.
        """
        symbols = []
        for child in node.children:
            parsed = self._parse_node(child, source_bytes)
            if parsed:
                symbols.extend(parsed) if isinstance(parsed, list) else symbols.append(parsed)
            elif child.type in self._container_types:
                symbols.extend(self._extract_symbols(child, source_bytes))
        return symbols

    def _parse_class(self, node: "Node", source_bytes: bytes) -> Symbol:
        """Parse a class declaration.

        Args:
            node: Class declaration node.
            source_bytes: Original source code as bytes.

        Returns:
            Symbol representing the class.
        """
        name = self._get_node_text(self._find_child(node, "type_identifier"), source_bytes)
        if not name:
            name = self._get_node_text(self._find_child(node, "identifier"), source_bytes)

        children = []
        body = self._find_child(node, "class_body")
        if body:
            for member in body.children:
                child_symbol = self._parse_class_member(member, source_bytes)
                if child_symbol:
                    children.append(child_symbol)

        return Symbol(
            name=name or "<anonymous>",
            type="class",
            lines=(node.start_point[0] + 1, node.end_point[0] + 1),
            docstring=self._get_preceding_comment(node, source_bytes),
            children=children,
        )

    def _parse_class_member(self, node: "Node", source_bytes: bytes) -> Optional[Symbol]:
        """Parse a class member (method, property).

        Args:
            node: Class member node.
            source_bytes: Original source code as bytes.

        Returns:
            Symbol or None.
        """
        if node.type == "method_definition":
            return self._parse_method(node, source_bytes)
        elif node.type == "abstract_method_signature":
            return self._parse_abstract_method(node, source_bytes)
        elif node.type == "public_field_definition":
            # Extract arrow functions assigned to class properties
            return self._parse_field_arrow_function(node, source_bytes)
        return None

    def _parse_method(self, node: "Node", source_bytes: bytes) -> Symbol:
        """Parse a method definition.

        Args:
            node: Method definition node.
            source_bytes: Original source code as bytes.

        Returns:
            Symbol representing the method.
        """
        name_node = self._find_child(node, "property_identifier")
        name = self._get_node_text(name_node, source_bytes) if name_node else "<anonymous>"

        # Check if async
        is_async = any(c.type == "async" for c in node.children)
        symbol_type = "async_method" if is_async else "method"

        signature = self._get_function_signature(node, source_bytes)

        return Symbol(
            name=name,
            type=symbol_type,
            lines=(node.start_point[0] + 1, node.end_point[0] + 1),
            signature=signature,
            docstring=self._get_preceding_comment(node, source_bytes),
        )

    def _parse_abstract_method(self, node: "Node", source_bytes: bytes) -> Symbol:
        """Parse an abstract method signature."""
        name_node = self._find_child(node, "property_identifier")
        name = self._get_node_text(name_node, source_bytes) if name_node else "<anonymous>"
        signature = self._get_function_signature(node, source_bytes)
        return Symbol(
            name=name,
            type="method",
            lines=(node.start_point[0] + 1, node.end_point[0] + 1),
            signature=signature,
            docstring=self._get_preceding_comment(node, source_bytes),
        )

    def _parse_field_arrow_function(self, node: "Node", source_bytes: bytes) -> Optional[Symbol]:
        """Parse a class field that is an arrow function."""
        name_node = self._find_child(node, "property_identifier")
        arrow_node = self._find_child(node, "arrow_function")
        if not (name_node and arrow_node):
            return None
        name = self._get_node_text(name_node, source_bytes)
        is_async = any(c.type == "async" for c in arrow_node.children)
        symbol_type = "async_method" if is_async else "method"
        signature = self._get_arrow_signature(arrow_node, source_bytes)
        return Symbol(
            name=name or "<anonymous>",
            type=symbol_type,
            lines=(node.start_point[0] + 1, node.end_point[0] + 1),
            signature=signature,
            docstring=self._get_preceding_comment(node, source_bytes),
        )

    def _parse_function(self, node: "Node", source_bytes: bytes, base_type: str) -> Symbol:
        """Parse a function declaration.

        Args:
            node: Function declaration node.
            source_bytes: Original source code as bytes.
            base_type: Base type (function or method).

        Returns:
            Symbol representing the function.
        """
        name_node = self._find_child(node, "identifier")
        name = self._get_node_text(name_node, source_bytes) if name_node else "<anonymous>"

        # Check if async
        is_async = any(c.type == "async" for c in node.children)
        symbol_type = f"async_{base_type}" if is_async else base_type

        signature = self._get_function_signature(node, source_bytes)

        return Symbol(
            name=name,
            type=symbol_type,
            lines=(node.start_point[0] + 1, node.end_point[0] + 1),
            signature=signature,
            docstring=self._get_preceding_comment(node, source_bytes),
        )

    def _parse_lexical_declaration(self, node: "Node", source_bytes: bytes) -> list[Symbol]:
        """Parse a const/let/var declaration for arrow functions.

        Args:
            node: Lexical or variable declaration node.
            source_bytes: Original source code as bytes.

        Returns:
            List of Symbols for named arrow functions found.
        """
        symbols = []
        for child in node.children:
            if child.type == "variable_declarator":
                name_node = self._find_child(child, "identifier")
                value_node = None
                for c in child.children:
                    if c.type == "arrow_function":
                        value_node = c
                        break
                    # Handle: const fn: Type = () => {} (function_expression too)
                    if c.type == "as_expression":
                        for cc in c.children:
                            if cc.type == "arrow_function":
                                value_node = cc
                                break

                if name_node and value_node:
                    name = self._get_node_text(name_node, source_bytes)
                    is_async = any(c.type == "async" for c in value_node.children)
                    symbol_type = "async_function" if is_async else "function"

                    signature = self._get_arrow_signature(value_node, source_bytes)

                    symbols.append(Symbol(
                        name=name or "<anonymous>",
                        type=symbol_type,
                        lines=(node.start_point[0] + 1, node.end_point[0] + 1),
                        signature=signature,
                        docstring=self._get_preceding_comment(node, source_bytes),
                    ))
        return symbols

    def _parse_interface(self, node: "Node", source_bytes: bytes) -> Symbol:
        """Parse an interface declaration.

        Args:
            node: Interface declaration node.
            source_bytes: Original source code as bytes.

        Returns:
            Symbol representing the interface.
        """
        name_node = self._find_child(node, "type_identifier")
        name = self._get_node_text(name_node, source_bytes) if name_node else "<anonymous>"

        return Symbol(
            name=name,
            type="interface",
            lines=(node.start_point[0] + 1, node.end_point[0] + 1),
            docstring=self._get_preceding_comment(node, source_bytes),
        )

    def _parse_type_alias(self, node: "Node", source_bytes: bytes) -> Symbol:
        """Parse a type alias declaration.

        Args:
            node: Type alias declaration node.
            source_bytes: Original source code as bytes.

        Returns:
            Symbol representing the type alias.
        """
        name_node = self._find_child(node, "type_identifier")
        name = self._get_node_text(name_node, source_bytes) if name_node else "<anonymous>"

        return Symbol(
            name=name,
            type="type",
            lines=(node.start_point[0] + 1, node.end_point[0] + 1),
            docstring=self._get_preceding_comment(node, source_bytes),
        )

    def _parse_enum(self, node: "Node", source_bytes: bytes) -> Symbol:
        """Parse an enum declaration.

        Args:
            node: Enum declaration node.
            source_bytes: Original source code as bytes.

        Returns:
            Symbol representing the enum.
        """
        name_node = self._find_child(node, "identifier")
        name = self._get_node_text(name_node, source_bytes) if name_node else "<anonymous>"

        return Symbol(
            name=name,
            type="enum",
            lines=(node.start_point[0] + 1, node.end_point[0] + 1),
            docstring=self._get_preceding_comment(node, source_bytes),
        )

    def _get_function_signature(self, node: "Node", source_bytes: bytes) -> str:
        """Extract function signature from a function/method node.

        Args:
            node: Function or method node.
            source_bytes: Original source code as bytes.

        Returns:
            Signature string.
        """
        params_node = self._find_child(node, "formal_parameters")
        if not params_node:
            return "()"

        params_text = self._get_node_text(params_node, source_bytes)

        # Get return type if present
        return_type = ""
        for child in node.children:
            if child.type == "type_annotation":
                return_type = self._get_node_text(child, source_bytes)
                break

        sig = params_text or "()"
        if return_type:
            sig += f" {return_type}"

        return sig

    def _get_arrow_signature(self, node: "Node", source_bytes: bytes) -> str:
        """Extract signature from an arrow function.

        Args:
            node: Arrow function node.
            source_bytes: Original source code as bytes.

        Returns:
            Signature string.
        """
        params_node = self._find_child(node, "formal_parameters")
        if params_node:
            params_text = self._get_node_text(params_node, source_bytes)
        else:
            # Single parameter without parens
            param_node = self._find_child(node, "identifier")
            params_text = f"({self._get_node_text(param_node, source_bytes)})" if param_node else "()"

        # Get return type if present
        return_type = ""
        for child in node.children:
            if child.type == "type_annotation":
                return_type = self._get_node_text(child, source_bytes)
                break

        sig = params_text
        if return_type:
            sig += f" {return_type}"

        return sig

    def _find_child(self, node: "Node", child_type: str) -> Optional["Node"]:
        """Find a child node by type.

        Args:
            node: Parent node.
            child_type: Type of child to find.

        Returns:
            Child node or None.
        """
        for child in node.children:
            if child.type == child_type:
                return child
        return None

    def _get_node_text(self, node: Optional["Node"], source_bytes: bytes) -> str:
        """Get the text content of a node.

        Args:
            node: Tree-sitter node.
            source_bytes: Original source code as bytes.

        Returns:
            Text content of the node.
        """
        if node is None:
            return ""
        return source_bytes[node.start_byte:node.end_byte].decode("utf-8")

    def _get_preceding_comment(self, node: "Node", source_bytes: bytes) -> Optional[str]:
        """Get JSDoc comment preceding a node.

        Args:
            node: Tree-sitter node.
            source_bytes: Original source code as bytes.

        Returns:
            Comment text or None.
        """
        # Look for comment in preceding siblings
        if node.prev_sibling and node.prev_sibling.type == "comment":
            comment = self._get_node_text(node.prev_sibling, source_bytes)
            # Clean up JSDoc comment
            if comment.startswith("/**"):
                comment = comment[3:-2].strip()
                # Remove leading * from lines
                lines = comment.split("\n")
                cleaned = []
                for line in lines:
                    line = line.strip()
                    if line.startswith("*"):
                        line = line[1:].strip()
                    if line and not line.startswith("@"):
                        cleaned.append(line)
                return " ".join(cleaned) if cleaned else None
            elif comment.startswith("//"):
                return comment[2:].strip()
        return None
