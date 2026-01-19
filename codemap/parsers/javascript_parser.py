"""JavaScript parser using tree-sitter."""

from __future__ import annotations

from typing import Optional

from .base import Parser, Symbol

# Tree-sitter imports - optional dependency
try:
    import tree_sitter_javascript as tsjs
    from tree_sitter import Language, Parser as TSParser, Node

    TREE_SITTER_AVAILABLE = True
except ImportError:
    TREE_SITTER_AVAILABLE = False
    TSParser = None
    Node = None


class JavaScriptParser(Parser):
    """Parser for JavaScript files using tree-sitter."""

    extensions = [".js", ".jsx", ".mjs", ".cjs"]
    language = "javascript"

    def __init__(self):
        """Initialize the JavaScript parser."""
        if not TREE_SITTER_AVAILABLE:
            raise ImportError(
                "tree-sitter and tree-sitter-javascript are required. "
                "Install with: pip install tree-sitter tree-sitter-javascript"
            )
        self._parser = TSParser(Language(tsjs.language()))

    def parse(self, source: str, filepath: str = "") -> list[Symbol]:
        """Parse JavaScript source code and extract symbols.

        Args:
            source: JavaScript source code.
            filepath: Optional file path.

        Returns:
            List of top-level Symbol objects.
        """
        # Convert to bytes for tree-sitter (it uses byte offsets)
        source_bytes = source.encode("utf-8")
        tree = self._parser.parse(source_bytes)
        return self._extract_symbols(tree.root_node, source_bytes)

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
            symbol = self._parse_node(child, source_bytes)
            if symbol:
                symbols.append(symbol)
            # Handle export statements
            elif child.type == "export_statement":
                exported = self._parse_export(child, source_bytes)
                if exported:
                    symbols.extend(exported)

        return symbols

    def _parse_node(self, node: "Node", source_bytes: bytes) -> Optional[Symbol]:
        """Parse a single node into a Symbol.

        Args:
            node: Tree-sitter node.
            source_bytes: Original source code as bytes.

        Returns:
            Symbol or None if not a recognized symbol type.
        """
        if node.type == "class_declaration":
            return self._parse_class(node, source_bytes)
        elif node.type == "function_declaration":
            return self._parse_function(node, source_bytes, "function")
        elif node.type in ("lexical_declaration", "variable_declaration"):
            # Handle const/let/var arrow functions
            return self._parse_variable_declaration(node, source_bytes)
        elif node.type == "expression_statement":
            # Handle CommonJS patterns: app.method = function() {}
            return self._parse_expression_statement(node, source_bytes)
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
            symbol = self._parse_node(child, source_bytes)
            if symbol:
                symbols.append(symbol)
            # Handle default exports
            elif child.type == "class":
                symbols.append(self._parse_class(child, source_bytes))
            elif child.type == "function":
                symbols.append(self._parse_function(child, source_bytes, "function"))
        return symbols

    def _parse_class(self, node: "Node", source_bytes: bytes) -> Symbol:
        """Parse a class declaration.

        Args:
            node: Class declaration node.
            source_bytes: Original source code as bytes.

        Returns:
            Symbol representing the class.
        """
        name_node = self._find_child(node, "identifier")
        name = self._get_node_text(name_node, source_bytes) if name_node else "<anonymous>"

        children = []
        body = self._find_child(node, "class_body")
        if body:
            for member in body.children:
                child_symbol = self._parse_class_member(member, source_bytes)
                if child_symbol:
                    children.append(child_symbol)

        return Symbol(
            name=name,
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
        elif node.type == "field_definition":
            # Check if it's an arrow function field
            for child in node.children:
                if child.type == "arrow_function":
                    name_node = self._find_child(node, "property_identifier")
                    name = self._get_node_text(name_node, source_bytes) if name_node else "<anonymous>"
                    is_async = any(c.type == "async" for c in child.children)
                    return Symbol(
                        name=name,
                        type="async_method" if is_async else "method",
                        lines=(node.start_point[0] + 1, node.end_point[0] + 1),
                        signature=self._get_arrow_signature(child, source_bytes),
                        docstring=self._get_preceding_comment(node, source_bytes),
                    )
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

        # Check if async or generator
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

        # Check if async or generator
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

    def _parse_variable_declaration(self, node: "Node", source_bytes: bytes) -> Optional[Symbol]:
        """Parse a const/let/var declaration for arrow functions.

        Args:
            node: Variable declaration node.
            source_bytes: Original source code as bytes.

        Returns:
            Symbol if it's a named arrow function, None otherwise.
        """
        for child in node.children:
            if child.type == "variable_declarator":
                name_node = self._find_child(child, "identifier")
                value_node = None
                for c in child.children:
                    if c.type == "arrow_function":
                        value_node = c
                        break
                    elif c.type in ("function", "function_expression"):
                        value_node = c
                        break

                if name_node and value_node:
                    name = self._get_node_text(name_node, source_bytes)
                    is_async = any(c.type == "async" for c in value_node.children)
                    symbol_type = "async_function" if is_async else "function"

                    if value_node.type == "arrow_function":
                        signature = self._get_arrow_signature(value_node, source_bytes)
                    else:
                        signature = self._get_function_signature(value_node, source_bytes)

                    return Symbol(
                        name=name or "<anonymous>",
                        type=symbol_type,
                        lines=(node.start_point[0] + 1, node.end_point[0] + 1),
                        signature=signature,
                        docstring=self._get_preceding_comment(node, source_bytes),
                    )
        return None

    def _parse_expression_statement(
        self, node: "Node", source_bytes: bytes
    ) -> Optional[Symbol]:
        """Parse an expression statement for CommonJS function assignments.

        Handles patterns like:
            app.method = function() {}
            obj.prop = () => {}
            module.exports.foo = function() {}

        Args:
            node: Expression statement node.
            source_bytes: Original source code as bytes.

        Returns:
            Symbol if it's a function assignment, None otherwise.
        """
        # Find the assignment expression
        assign_node = self._find_child(node, "assignment_expression")
        if not assign_node:
            return None

        # Get left side (should be member_expression) and right side (function)
        left_node = None
        right_node = None
        for child in assign_node.children:
            if child.type == "member_expression":
                left_node = child
            elif child.type in ("function_expression", "arrow_function", "function"):
                right_node = child

        if not left_node or not right_node:
            return None

        # Extract method name from property_identifier
        name = None
        for child in left_node.children:
            if child.type == "property_identifier":
                name = self._get_node_text(child, source_bytes)
                break

        # Fallback to named function expression if available
        if not name and right_node.type in ("function_expression", "function"):
            name_node = self._find_child(right_node, "identifier")
            if name_node:
                name = self._get_node_text(name_node, source_bytes)

        if not name:
            return None

        # Determine if async
        is_async = any(c.type == "async" for c in right_node.children)
        symbol_type = "async_function" if is_async else "function"

        # Get signature
        if right_node.type == "arrow_function":
            signature = self._get_arrow_signature(right_node, source_bytes)
        else:
            signature = self._get_function_signature(right_node, source_bytes)

        return Symbol(
            name=name,
            type=symbol_type,
            lines=(node.start_point[0] + 1, node.end_point[0] + 1),
            signature=signature,
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

        return self._get_node_text(params_node, source_bytes) or "()"

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
            return self._get_node_text(params_node, source_bytes) or "()"
        else:
            # Single parameter without parens
            param_node = self._find_child(node, "identifier")
            if param_node:
                return f"({self._get_node_text(param_node, source_bytes)})"
            return "()"

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
