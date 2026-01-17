"""C++ parser using tree-sitter with configuration-driven extraction."""

from __future__ import annotations

from .treesitter_base import TreeSitterParser, LanguageConfig, NodeMapping
from .base import Symbol


CPP_CONFIG = LanguageConfig(
    name="cpp",
    extensions=[".cpp", ".hpp", ".cc", ".hh", ".cxx", ".hxx", ".h"],
    grammar_module="cpp",
    node_mappings={
        # Classes
        "class_specifier": NodeMapping(
            symbol_type="class",
            name_child="type_identifier",
            body_child="field_declaration_list",
        ),
        # Structs
        "struct_specifier": NodeMapping(
            symbol_type="struct",
            name_child="type_identifier",
            body_child="field_declaration_list",
        ),
        # Namespaces
        "namespace_definition": NodeMapping(
            symbol_type="namespace",
            name_child="namespace_identifier",
            body_child="declaration_list",
        ),
        # Enums
        "enum_specifier": NodeMapping(
            symbol_type="enum",
            name_child="type_identifier",
            body_child="enumerator_list",
        ),
        # Functions (top-level)
        "function_definition": NodeMapping(
            symbol_type="function",
            name_child="function_declarator/identifier",
            body_child="compound_statement",
            signature_child="function_declarator/parameter_list",
        ),
        # Template declarations
        "template_declaration": NodeMapping(
            symbol_type="template",
            name_child=None,  # Handled specially
        ),
    },
    comment_types=["comment"],
    doc_comment_prefix="/**",
)


class CppParser(TreeSitterParser):
    """Parser for C++ files using tree-sitter.

    Supports:
    - Classes and structs
    - Namespaces
    - Enums (including enum class)
    - Functions and methods
    - Templates
    """

    config = CPP_CONFIG
    extensions = [".cpp", ".hpp", ".cc", ".hh", ".cxx", ".hxx"]
    language = "cpp"

    def _get_child_by_type(self, node, child_type: str):
        """Get first child of a given type."""
        for child in node.children:
            if child.type == child_type:
                return child
        return None

    def _get_name_from_path(self, node, path: str, source_bytes: bytes) -> str | None:
        """Get name from a path like 'function_declarator/identifier'."""
        parts = path.split("/")
        current = node
        for part in parts:
            found = False
            for child in current.children:
                if child.type == part:
                    current = child
                    found = True
                    break
            if not found:
                return None
        return source_bytes[current.start_byte:current.end_byte].decode("utf-8")

    def _extract_methods(self, body_node, source_bytes: bytes) -> list[Symbol]:
        """Extract methods from a class/struct body."""
        methods = []
        if body_node is None:
            return methods

        for child in body_node.children:
            if child.type == "function_definition":
                method = self._extract_method(child, source_bytes)
                if method:
                    methods.append(method)
        return methods

    def _extract_method(self, node, source_bytes: bytes) -> Symbol | None:
        """Extract a method from a function_definition node."""
        # Get name from function_declarator
        name = None
        signature = None

        for child in node.children:
            if child.type == "function_declarator":
                for subchild in child.children:
                    if subchild.type in ("identifier", "field_identifier"):
                        name = source_bytes[subchild.start_byte:subchild.end_byte].decode("utf-8")
                    elif subchild.type == "parameter_list":
                        signature = source_bytes[subchild.start_byte:subchild.end_byte].decode("utf-8")
            # Handle pointer return types
            elif child.type == "pointer_declarator":
                for subchild in child.children:
                    if subchild.type == "function_declarator":
                        for subsubchild in subchild.children:
                            if subsubchild.type in ("identifier", "field_identifier"):
                                name = source_bytes[subsubchild.start_byte:subsubchild.end_byte].decode("utf-8")
                            elif subsubchild.type == "parameter_list":
                                signature = source_bytes[subsubchild.start_byte:subsubchild.end_byte].decode("utf-8")

        if not name:
            return None

        docstring = self._extract_docstring(node, source_bytes)

        return Symbol(
            name=name,
            type="method",
            lines=(node.start_point[0] + 1, node.end_point[0] + 1),
            signature=signature,
            docstring=docstring,
            children=None,
        )

    def _extract_symbol(self, node, source_bytes):
        """Override to handle C++-specific node structures."""
        mapping = self.config.node_mappings.get(node.type)
        if not mapping:
            return None

        # Handle class_specifier and struct_specifier
        if node.type in ("class_specifier", "struct_specifier"):
            name = None
            for child in node.children:
                if child.type == "type_identifier":
                    name = source_bytes[child.start_byte:child.end_byte].decode("utf-8")
                    break

            # Skip anonymous classes/structs
            if not name:
                return None

            # Extract methods
            body = self._get_child_by_type(node, "field_declaration_list")
            methods = self._extract_methods(body, source_bytes)

            docstring = self._extract_docstring(node, source_bytes)
            symbol_type = "class" if node.type == "class_specifier" else "struct"

            return Symbol(
                name=name,
                type=symbol_type,
                lines=(node.start_point[0] + 1, node.end_point[0] + 1),
                signature=None,
                docstring=docstring,
                children=methods if methods else None,
            )

        # Handle namespace_definition
        if node.type == "namespace_definition":
            name = None
            for child in node.children:
                if child.type == "namespace_identifier":
                    name = source_bytes[child.start_byte:child.end_byte].decode("utf-8")
                    break

            # Skip anonymous namespaces
            if not name:
                return None

            # Extract children (classes, functions, etc.)
            body = self._get_child_by_type(node, "declaration_list")
            children = []
            if body:
                for child in body.children:
                    child_symbol = self._extract_symbol(child, source_bytes)
                    if child_symbol:
                        children.append(child_symbol)

            docstring = self._extract_docstring(node, source_bytes)

            return Symbol(
                name=name,
                type="namespace",
                lines=(node.start_point[0] + 1, node.end_point[0] + 1),
                signature=None,
                docstring=docstring,
                children=children if children else None,
            )

        # Handle enum_specifier
        if node.type == "enum_specifier":
            name = None
            for child in node.children:
                if child.type == "type_identifier":
                    name = source_bytes[child.start_byte:child.end_byte].decode("utf-8")
                    break

            # Skip anonymous enums
            if not name:
                return None

            docstring = self._extract_docstring(node, source_bytes)

            return Symbol(
                name=name,
                type="enum",
                lines=(node.start_point[0] + 1, node.end_point[0] + 1),
                signature=None,
                docstring=docstring,
                children=None,
            )

        # Handle function_definition (top-level functions)
        if node.type == "function_definition":
            method = self._extract_method(node, source_bytes)
            if method:
                # Change type from method to function for top-level
                return Symbol(
                    name=method.name,
                    type="function",
                    lines=method.lines,
                    signature=method.signature,
                    docstring=method.docstring,
                    children=None,
                )
            return None

        # Handle template_declaration
        if node.type == "template_declaration":
            # Find the inner declaration (class, function, etc.)
            for child in node.children:
                if child.type in ("class_specifier", "struct_specifier", "function_definition"):
                    inner_symbol = self._extract_symbol(child, source_bytes)
                    if inner_symbol:
                        # Mark as template
                        return Symbol(
                            name=inner_symbol.name,
                            type=f"template_{inner_symbol.type}",
                            lines=(node.start_point[0] + 1, node.end_point[0] + 1),
                            signature=inner_symbol.signature,
                            docstring=inner_symbol.docstring,
                            children=inner_symbol.children,
                        )
            return None

        return super()._extract_symbol(node, source_bytes)
