"""C# parser using tree-sitter with configuration-driven extraction."""

from __future__ import annotations

from .treesitter_base import TreeSitterParser, LanguageConfig, NodeMapping


def _is_async_csharp(node) -> bool:
    """Check if a C# method is async."""
    for child in node.children:
        if child.type == "modifier" and child.text == b"async":
            return True
    return False


CSHARP_CONFIG = LanguageConfig(
    name="csharp",
    extensions=[".cs"],
    grammar_module="c_sharp",
    container_types=[
        "namespace_declaration",              # namespace Foo { ... }
        "file_scoped_namespace_declaration",  # namespace Foo; (C# 10+)
        "declaration_list",                   # { ... } block containing declarations
    ],
    node_mappings={
        "class_declaration": NodeMapping(
            symbol_type="class",
            name_child="identifier",
            body_child="declaration_list",
        ),
        "interface_declaration": NodeMapping(
            symbol_type="interface",
            name_child="identifier",
            body_child="declaration_list",
        ),
        "struct_declaration": NodeMapping(
            symbol_type="struct",
            name_child="identifier",
            body_child="declaration_list",
        ),
        "enum_declaration": NodeMapping(
            symbol_type="enum",
            name_child="identifier",
            body_child="enum_member_declaration_list",
        ),
        "method_declaration": NodeMapping(
            symbol_type="method",
            name_child="identifier",
            signature_child="parameter_list",
            is_async_check=_is_async_csharp,
        ),
        "constructor_declaration": NodeMapping(
            symbol_type="method",
            name_child="identifier",
            signature_child="parameter_list",
        ),
        "property_declaration": NodeMapping(
            symbol_type="property",
            name_child="identifier",
        ),
    },
    comment_types=["comment"],
    doc_comment_prefix="///",
)


class CSharpParser(TreeSitterParser):
    """Parser for C# files using tree-sitter."""

    config = CSHARP_CONFIG
