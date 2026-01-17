"""C parser using tree-sitter with configuration-driven extraction."""

from __future__ import annotations

from .treesitter_base import TreeSitterParser, LanguageConfig, NodeMapping


C_CONFIG = LanguageConfig(
    name="c",
    extensions=[".c", ".h"],
    grammar_module="c",
    node_mappings={
        # Functions
        "function_definition": NodeMapping(
            symbol_type="function",
            name_child="function_declarator/identifier",
            body_child="compound_statement",
            signature_child="function_declarator/parameter_list",
        ),
        # Structs
        "struct_specifier": NodeMapping(
            symbol_type="struct",
            name_child="type_identifier",
            body_child="field_declaration_list",
        ),
        # Enums
        "enum_specifier": NodeMapping(
            symbol_type="enum",
            name_child="type_identifier",
            body_child="enumerator_list",
        ),
        # Typedefs (we'll handle specially)
        "type_definition": NodeMapping(
            symbol_type="typedef",
            name_child="type_identifier",
        ),
    },
    comment_types=["comment"],
    doc_comment_prefix="/*",
)


class CParser(TreeSitterParser):
    """Parser for C files using tree-sitter.

    Supports:
    - Functions
    - Structs
    - Enums
    - Typedefs
    """

    config = C_CONFIG
    extensions = [".c", ".h"]
    language = "c"

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

    def _extract_symbol(self, node, source_bytes):
        """Override to handle C-specific node structures."""
        mapping = self.config.node_mappings.get(node.type)
        if not mapping:
            return None

        # Handle function_definition specially due to nested name
        if node.type == "function_definition":
            # Try different paths for function name (handles pointer return types)
            name = self._get_name_from_path(node, "function_declarator/identifier", source_bytes)
            if not name:
                # Pointer return type: int* func() has pointer_declarator wrapping function_declarator
                name = self._get_name_from_path(node, "pointer_declarator/function_declarator/identifier", source_bytes)
            if not name:
                # Try declarator for other cases
                name = self._get_name_from_path(node, "declarator/identifier", source_bytes)
            if not name:
                return None

            # Get signature from parameter list (handle both direct and pointer cases)
            signature = None
            for child in node.children:
                if child.type == "function_declarator":
                    for subchild in child.children:
                        if subchild.type == "parameter_list":
                            signature = source_bytes[subchild.start_byte:subchild.end_byte].decode("utf-8")
                            break
                elif child.type == "pointer_declarator":
                    for subchild in child.children:
                        if subchild.type == "function_declarator":
                            for subsubchild in subchild.children:
                                if subsubchild.type == "parameter_list":
                                    signature = source_bytes[subsubchild.start_byte:subsubchild.end_byte].decode("utf-8")
                                    break

            docstring = self._extract_docstring(node, source_bytes)

            from .base import Symbol
            return Symbol(
                name=name,
                type="function",
                lines=(node.start_point[0] + 1, node.end_point[0] + 1),
                signature=signature,
                docstring=docstring,
                children=None,
            )

        # Handle struct_specifier and enum_specifier
        if node.type in ("struct_specifier", "enum_specifier"):
            name = None
            for child in node.children:
                if child.type == "type_identifier":
                    name = source_bytes[child.start_byte:child.end_byte].decode("utf-8")
                    break

            # Skip anonymous structs/enums
            if not name:
                return None

            docstring = self._extract_docstring(node, source_bytes)
            symbol_type = "struct" if node.type == "struct_specifier" else "enum"

            from .base import Symbol
            return Symbol(
                name=name,
                type=symbol_type,
                lines=(node.start_point[0] + 1, node.end_point[0] + 1),
                signature=None,
                docstring=docstring,
                children=None,
            )

        # Handle type_definition (typedef)
        if node.type == "type_definition":
            # Find the new type name (last identifier or type_identifier)
            name = None
            for child in node.children:
                if child.type == "type_identifier":
                    name = source_bytes[child.start_byte:child.end_byte].decode("utf-8")
                elif child.type == "identifier":
                    name = source_bytes[child.start_byte:child.end_byte].decode("utf-8")

            if not name:
                return None

            docstring = self._extract_docstring(node, source_bytes)

            from .base import Symbol
            return Symbol(
                name=name,
                type="typedef",
                lines=(node.start_point[0] + 1, node.end_point[0] + 1),
                signature=None,
                docstring=docstring,
                children=None,
            )

        return super()._extract_symbol(node, source_bytes)
