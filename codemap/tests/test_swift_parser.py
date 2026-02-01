"""Tests for the Swift parser."""

import pytest

# Skip all tests if tree-sitter-swift is not installed
pytest.importorskip("tree_sitter_swift")

from codemap.parsers.swift_parser import SwiftParser


class TestSwiftParser:
    """Tests for SwiftParser class."""

    @pytest.fixture
    def parser(self):
        return SwiftParser()

    def test_parse_simple_struct(self, parser):
        source = '''
struct User {
    let id: Int
    let name: String
}
'''
        symbols = parser.parse(source)

        assert len(symbols) == 1
        assert symbols[0].name == "User"
        assert symbols[0].type == "class"

    def test_parse_class(self, parser):
        source = '''
class AppConfig {
    let version = "1.0.0"
}
'''
        symbols = parser.parse(source)

        assert len(symbols) == 1
        assert symbols[0].name == "AppConfig"
        assert symbols[0].type == "class"

    def test_parse_class_with_methods(self, parser):
        source = '''
class Calculator {
    func add(a: Int, b: Int) -> Int {
        return a + b
    }

    func subtract(a: Int, b: Int) -> Int {
        return a - b
    }
}
'''
        symbols = parser.parse(source)

        assert len(symbols) == 1
        calc = symbols[0]
        assert calc.name == "Calculator"
        assert calc.type == "class"
        assert len(calc.children) == 2
        assert calc.children[0].name == "add"
        assert calc.children[0].type == "method"
        assert calc.children[1].name == "subtract"

    def test_parse_protocol(self, parser):
        source = '''
protocol UserService {
    func getUser(id: Int) -> User?
    func createUser(name: String) -> User
}
'''
        symbols = parser.parse(source)

        assert len(symbols) == 1
        assert symbols[0].name == "UserService"
        assert symbols[0].type == "interface"

    def test_parse_enum(self, parser):
        source = '''
enum Status {
    case active
    case inactive
    case pending
}
'''
        symbols = parser.parse(source)

        assert len(symbols) == 1
        assert symbols[0].name == "Status"
        assert symbols[0].type == "enum"

    def test_parse_top_level_function(self, parser):
        source = '''
func validateEmail(_ email: String) -> Bool {
    return email.contains("@")
}

func formatName(_ name: String) -> String {
    return name.trimmingCharacters(in: .whitespaces)
}
'''
        symbols = parser.parse(source)

        assert len(symbols) == 2
        assert symbols[0].name == "validateEmail"
        assert symbols[0].type == "function"
        assert symbols[1].name == "formatName"
        assert symbols[1].type == "function"

    def test_parse_multiple_types(self, parser):
        source = '''
struct First {
    func method1() {}
}

class Second {
    func method2() {}
}

protocol Third {
    func method3()
}
'''
        symbols = parser.parse(source)

        assert len(symbols) == 3
        names = [s.name for s in symbols]
        assert "First" in names
        assert "Second" in names
        assert "Third" in names

    def test_parse_fixture_file(self, parser):
        """Test parsing the Swift fixture file."""
        import os
        fixture_path = os.path.join(
            os.path.dirname(__file__), "fixtures", "SampleModule.swift"
        )
        with open(fixture_path, "r") as f:
            source = f.read()

        symbols = parser.parse(source, fixture_path)

        # Should find multiple symbols (structs, classes, protocols, enums, functions)
        assert len(symbols) >= 4

        names = [s.name for s in symbols]
        assert "User" in names
        assert "UserService" in names
        assert "DefaultUserService" in names

    def test_extensions(self, parser):
        """Test that the parser handles the correct extensions."""
        assert ".swift" in parser.extensions

    def test_language(self, parser):
        """Test that the parser reports the correct language."""
        assert parser.language == "swift"

    def test_extension_methods_classified_as_methods(self, parser):
        """Extension methods should be classified as methods, not functions."""
        source = '''
extension Foo {
    func helper() {}
    func another() -> Int { return 0 }
}
'''
        symbols = parser.parse(source)
        assert len(symbols) == 1
        assert symbols[0].name == "Foo"
        assert symbols[0].type == "class"
        assert len(symbols[0].children) == 2
        for child in symbols[0].children:
            assert child.type == "method"

    def test_preprocessor_directives_do_not_break_parsing(self, parser):
        """#if/#endif directives should not cause methods to be misclassified."""
        source = '''
public class MyClass: Base {
    func normalMethod() {}

    #if canImport(Foundation)
    func conditionalMethod() {}
    #endif

    func anotherMethod() {}
}
'''
        symbols = parser.parse(source)
        assert len(symbols) == 1
        cls = symbols[0]
        assert cls.name == "MyClass"
        assert cls.type == "class"
        # All functions inside the class should be methods
        assert len(cls.children) == 3
        for child in cls.children:
            assert child.type == "method", f"{child.name} should be method, got {child.type}"

    def test_enum_with_methods(self, parser):
        """Enum methods should be classified as methods."""
        source = '''
enum Direction {
    case north, south
    func description() -> String { return "" }
}
'''
        symbols = parser.parse(source)
        assert len(symbols) == 1
        assert symbols[0].type == "enum"
        assert len(symbols[0].children) == 1
        assert symbols[0].children[0].type == "method"
