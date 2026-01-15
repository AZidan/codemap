"""Tests for the C++ parser."""

import os

import pytest

# Skip all tests if tree-sitter-cpp is not installed
pytest.importorskip("tree_sitter_cpp")

from codemap.parsers.cpp_parser import CppParser


class TestCppParser:
    """Tests for CppParser class."""

    @pytest.fixture
    def parser(self):
        return CppParser()

    def test_parse_simple_class(self, parser):
        source = '''
/** A simple class. */
class Point {
public:
    int getX() const { return x_; }
private:
    int x_;
};
'''
        symbols = parser.parse(source)

        assert len(symbols) == 1
        assert symbols[0].name == "Point"
        assert symbols[0].type == "class"
        assert symbols[0].children is not None
        assert len(symbols[0].children) == 1
        assert symbols[0].children[0].name == "getX"
        assert symbols[0].children[0].type == "method"

    def test_parse_struct(self, parser):
        source = '''
/* A simple struct */
struct Vector {
    double x, y, z;
    double length() const { return 0; }
};
'''
        symbols = parser.parse(source)

        assert len(symbols) == 1
        assert symbols[0].name == "Vector"
        assert symbols[0].type == "struct"
        assert symbols[0].children is not None
        assert len(symbols[0].children) == 1

    def test_parse_namespace(self, parser):
        source = '''
namespace math {
    int add(int a, int b) { return a + b; }
}
'''
        symbols = parser.parse(source)

        assert len(symbols) == 1
        assert symbols[0].name == "math"
        assert symbols[0].type == "namespace"
        assert symbols[0].children is not None
        assert len(symbols[0].children) == 1
        assert symbols[0].children[0].name == "add"
        assert symbols[0].children[0].type == "function"

    def test_parse_namespace_with_class(self, parser):
        source = '''
namespace utils {
    class Helper {
    public:
        void help() {}
    };
}
'''
        symbols = parser.parse(source)

        assert len(symbols) == 1
        assert symbols[0].name == "utils"
        assert symbols[0].type == "namespace"
        assert symbols[0].children[0].name == "Helper"
        assert symbols[0].children[0].type == "class"

    def test_parse_enum(self, parser):
        source = '''
enum Status {
    Ok,
    Error
};
'''
        symbols = parser.parse(source)

        assert len(symbols) == 1
        assert symbols[0].name == "Status"
        assert symbols[0].type == "enum"

    def test_parse_enum_class(self, parser):
        source = '''
enum class Color {
    Red,
    Green,
    Blue
};
'''
        symbols = parser.parse(source)

        assert len(symbols) == 1
        assert symbols[0].name == "Color"
        assert symbols[0].type == "enum"

    def test_parse_template_class(self, parser):
        source = '''
template<typename T>
class Container {
public:
    void add(T item) {}
    size_t size() const { return 0; }
};
'''
        symbols = parser.parse(source)

        assert len(symbols) == 1
        assert symbols[0].name == "Container"
        assert symbols[0].type == "template_class"
        assert symbols[0].children is not None
        assert len(symbols[0].children) == 2

    def test_parse_template_function(self, parser):
        source = '''
template<typename T>
void swap(T& a, T& b) {
    T temp = a;
    a = b;
    b = temp;
}
'''
        symbols = parser.parse(source)

        assert len(symbols) == 1
        assert symbols[0].name == "swap"
        assert symbols[0].type == "template_function"

    def test_parse_top_level_function(self, parser):
        source = '''
/* Add two numbers */
int add(int a, int b) {
    return a + b;
}
'''
        symbols = parser.parse(source)

        assert len(symbols) == 1
        assert symbols[0].name == "add"
        assert symbols[0].type == "function"
        assert symbols[0].signature == "(int a, int b)"

    def test_parse_function_with_pointer_return(self, parser):
        source = '''
Point* createPoint() {
    return new Point();
}
'''
        symbols = parser.parse(source)

        assert len(symbols) == 1
        assert symbols[0].name == "createPoint"
        assert symbols[0].type == "function"

    def test_parse_multiple_classes(self, parser):
        source = '''
class A { void foo() {} };
class B { void bar() {} };
class C { void baz() {} };
'''
        symbols = parser.parse(source)

        assert len(symbols) == 3
        names = [s.name for s in symbols]
        assert "A" in names
        assert "B" in names
        assert "C" in names

    def test_skip_anonymous_class(self, parser):
        source = '''
class {
    int x;
} instance;
'''
        symbols = parser.parse(source)

        assert len(symbols) == 0

    def test_parse_fixture_file(self, parser):
        """Test parsing the C++ fixture file."""
        fixture_path = os.path.join(
            os.path.dirname(__file__), "fixtures", "sample_module.cpp"
        )
        with open(fixture_path, "r") as f:
            source = f.read()
        symbols = parser.parse(source, fixture_path)

        # Should find multiple symbols
        assert len(symbols) >= 8

        # Check for expected symbol types
        names = [s.name for s in symbols]
        types = [s.type for s in symbols]

        assert "Point" in names  # class
        assert "Vector3D" in names  # struct
        assert "Status" in names  # enum
        assert "math" in names  # namespace
        assert "Container" in names  # template class
        assert "main" in names  # function

        assert "class" in types
        assert "struct" in types
        assert "enum" in types
        assert "namespace" in types
        assert "template_class" in types
        assert "function" in types

    def test_docstring_extraction(self, parser):
        source = '''
/**
 * Calculate the sum.
 * @param a First number
 * @param b Second number
 * @return The sum
 */
int sum(int a, int b) {
    return a + b;
}
'''
        symbols = parser.parse(source)

        assert len(symbols) == 1
        assert symbols[0].docstring is not None
        assert "sum" in symbols[0].docstring.lower() or "Calculate" in symbols[0].docstring

    def test_parser_extensions(self, parser):
        """Test that parser handles correct extensions."""
        assert ".cpp" in parser.extensions
        assert ".hpp" in parser.extensions
        assert ".cc" in parser.extensions
        assert ".hh" in parser.extensions

    def test_parser_language(self, parser):
        """Test parser language property."""
        assert parser.language == "cpp"

    def test_class_with_constructor(self, parser):
        source = '''
class Point {
public:
    Point(int x, int y) : x_(x), y_(y) {}
    int getX() const { return x_; }
private:
    int x_, y_;
};
'''
        symbols = parser.parse(source)

        assert len(symbols) == 1
        assert symbols[0].name == "Point"
        assert len(symbols[0].children) == 2
        method_names = [m.name for m in symbols[0].children]
        assert "Point" in method_names  # constructor
        assert "getX" in method_names
