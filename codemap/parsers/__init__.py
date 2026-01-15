"""Language parsers for symbol extraction."""

from .base import Parser, Symbol
from .python_parser import PythonParser

__all__ = ["Parser", "Symbol", "PythonParser"]

# Optional tree-sitter parsers - each imports gracefully if grammar is available

try:
    from .typescript_parser import TypeScriptParser
    __all__.append("TypeScriptParser")
except ImportError:
    TypeScriptParser = None

try:
    from .javascript_parser import JavaScriptParser
    __all__.append("JavaScriptParser")
except ImportError:
    JavaScriptParser = None

try:
    from .go_parser import GoParser
    __all__.append("GoParser")
except ImportError:
    GoParser = None

try:
    from .java_parser import JavaParser
    __all__.append("JavaParser")
except ImportError:
    JavaParser = None

try:
    from .csharp_parser import CSharpParser
    __all__.append("CSharpParser")
except ImportError:
    CSharpParser = None

try:
    from .rust_parser import RustParser
    __all__.append("RustParser")
except ImportError:
    RustParser = None

try:
    from .kotlin_parser import KotlinParser
    __all__.append("KotlinParser")
except ImportError:
    KotlinParser = None

try:
    from .swift_parser import SwiftParser
    __all__.append("SwiftParser")
except ImportError:
    SwiftParser = None

try:
    from .c_parser import CParser
    __all__.append("CParser")
except ImportError:
    CParser = None

try:
    from .cpp_parser import CppParser
    __all__.append("CppParser")
except ImportError:
    CppParser = None


def get_available_parsers() -> list[type[Parser]]:
    """Return list of all available parser classes."""
    parsers = [PythonParser]

    if TypeScriptParser:
        parsers.append(TypeScriptParser)
    if JavaScriptParser:
        parsers.append(JavaScriptParser)
    if GoParser:
        parsers.append(GoParser)
    if JavaParser:
        parsers.append(JavaParser)
    if CSharpParser:
        parsers.append(CSharpParser)
    if RustParser:
        parsers.append(RustParser)
    if KotlinParser:
        parsers.append(KotlinParser)
    if SwiftParser:
        parsers.append(SwiftParser)
    if CParser:
        parsers.append(CParser)
    if CppParser:
        parsers.append(CppParser)

    return parsers


def get_parser_for_extension(ext: str) -> type[Parser] | None:
    """Get the appropriate parser class for a file extension."""
    for parser_cls in get_available_parsers():
        try:
            extensions = parser_cls.extensions
            # Handle property objects (need instance) vs class attributes
            if isinstance(extensions, property):
                continue
            if ext in extensions:
                return parser_cls
        except (TypeError, AttributeError):
            continue
    return None
