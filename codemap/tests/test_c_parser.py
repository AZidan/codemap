"""Tests for the C parser."""

import os

import pytest

# Skip all tests if tree-sitter-c is not installed
pytest.importorskip("tree_sitter_c")

from codemap.parsers.c_parser import CParser


class TestCParser:
    """Tests for CParser class."""

    @pytest.fixture
    def parser(self):
        return CParser()

    def test_parse_simple_function(self, parser):
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
/* Create an array */
int* create_array(size_t size) {
    return NULL;
}
'''
        symbols = parser.parse(source)

        assert len(symbols) == 1
        assert symbols[0].name == "create_array"
        assert symbols[0].type == "function"
        assert symbols[0].signature == "(size_t size)"

    def test_parse_void_function(self, parser):
        source = '''
void print_hello(void) {
    printf("Hello\\n");
}
'''
        symbols = parser.parse(source)

        assert len(symbols) == 1
        assert symbols[0].name == "print_hello"
        assert symbols[0].type == "function"

    def test_parse_struct(self, parser):
        source = '''
/* A 2D point */
struct Point {
    int x;
    int y;
};
'''
        symbols = parser.parse(source)

        assert len(symbols) == 1
        assert symbols[0].name == "Point"
        assert symbols[0].type == "struct"
        assert "2D point" in symbols[0].docstring

    def test_parse_enum(self, parser):
        source = '''
/* Status codes */
enum Status {
    OK = 0,
    ERROR = -1
};
'''
        symbols = parser.parse(source)

        assert len(symbols) == 1
        assert symbols[0].name == "Status"
        assert symbols[0].type == "enum"

    def test_parse_typedef_primitive(self, parser):
        source = '''
/* Byte type alias */
typedef unsigned char byte;
'''
        symbols = parser.parse(source)

        assert len(symbols) == 1
        assert symbols[0].name == "byte"
        assert symbols[0].type == "typedef"

    def test_parse_typedef_enum(self, parser):
        source = '''
enum Status { OK, ERROR };
typedef enum Status StatusCode;
'''
        symbols = parser.parse(source)

        assert len(symbols) == 2
        names = [s.name for s in symbols]
        types = [s.type for s in symbols]
        assert "Status" in names
        assert "StatusCode" in names
        assert "enum" in types
        assert "typedef" in types

    def test_parse_multiple_functions(self, parser):
        source = '''
int add(int a, int b) { return a + b; }
int sub(int a, int b) { return a - b; }
int mul(int a, int b) { return a * b; }
'''
        symbols = parser.parse(source)

        assert len(symbols) == 3
        names = [s.name for s in symbols]
        assert "add" in names
        assert "sub" in names
        assert "mul" in names

    def test_parse_nested_struct(self, parser):
        source = '''
struct Point {
    int x;
    int y;
};

struct Rectangle {
    struct Point top_left;
    struct Point bottom_right;
};
'''
        symbols = parser.parse(source)

        assert len(symbols) == 2
        names = [s.name for s in symbols]
        assert "Point" in names
        assert "Rectangle" in names

    def test_skip_anonymous_struct(self, parser):
        source = '''
struct {
    int x;
    int y;
} point;
'''
        symbols = parser.parse(source)

        # Anonymous struct should be skipped
        assert len(symbols) == 0

    def test_parse_fixture_file(self, parser):
        """Test parsing the C fixture file."""
        fixture_path = os.path.join(
            os.path.dirname(__file__), "fixtures", "sample_module.c"
        )
        with open(fixture_path, "r") as f:
            source = f.read()
        symbols = parser.parse(source, fixture_path)

        # Should find all symbols
        assert len(symbols) >= 10

        # Check for expected symbol types
        names = [s.name for s in symbols]
        types = [s.type for s in symbols]

        assert "Status" in names  # enum
        assert "Point" in names  # struct
        assert "Rectangle" in names  # struct
        assert "add" in names  # function
        assert "create_array" in names  # function with pointer return
        assert "main" in names  # main function

        assert "enum" in types
        assert "struct" in types
        assert "function" in types
        assert "typedef" in types

    def test_docstring_extraction(self, parser):
        source = '''
/**
 * Calculate the sum of two numbers.
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
        assert ".c" in parser.extensions
        assert ".h" in parser.extensions

    def test_parser_language(self, parser):
        """Test parser language property."""
        assert parser.language == "c"

    def test_function_with_struct_param(self, parser):
        source = '''
struct Point { int x; int y; };

void print_point(struct Point p) {
    printf("%d, %d\\n", p.x, p.y);
}
'''
        symbols = parser.parse(source)

        assert len(symbols) == 2
        func = next(s for s in symbols if s.type == "function")
        assert func.name == "print_point"
        assert "struct Point p" in func.signature

    def test_parse_header_with_include_guard(self, parser):
        """Test that symbols inside #ifndef include guards are extracted."""
        source = '''
#ifndef MY_HEADER_H
#define MY_HEADER_H

typedef unsigned char byte;

struct Point {
    int x;
    int y;
};

enum Status {
    OK,
    ERROR
};

static inline int add(int a, int b) {
    return a + b;
}

#endif
'''
        symbols = parser.parse(source, "test.h")

        names = [s.name for s in symbols]
        assert "byte" in names
        assert "Point" in names
        assert "Status" in names
        assert "add" in names
        assert len(symbols) == 4

    def test_parse_ifdef_else_blocks(self, parser):
        """Test that symbols inside #ifdef/#else blocks are extracted."""
        source = '''
#ifdef WIN32
int win_func(void) { return 1; }
#else
int unix_func(void) { return 2; }
#endif
'''
        symbols = parser.parse(source)

        names = [s.name for s in symbols]
        assert "win_func" in names
        assert "unix_func" in names

    def test_parse_preproc_if_elif(self, parser):
        """Test that symbols inside #if/#elif blocks are extracted."""
        source = '''
#if defined(DEBUG)
void debug_log(const char *msg) { }
#elif defined(VERBOSE)
void verbose_log(const char *msg) { }
#endif
'''
        symbols = parser.parse(source)

        names = [s.name for s in symbols]
        assert "debug_log" in names
        assert "verbose_log" in names

    def test_parse_mixed_preprocessor_and_toplevel(self, parser):
        """Test files with both preprocessor-wrapped and top-level symbols."""
        source = '''
#include <stdio.h>

int always_available(void) { return 1; }

#ifdef FEATURE_X
int feature_x_func(void) { return 2; }
#endif

struct Config {
    int value;
};
'''
        symbols = parser.parse(source)

        names = [s.name for s in symbols]
        assert "always_available" in names
        assert "feature_x_func" in names
        assert "Config" in names

    def test_parse_typedef_with_embedded_enum_in_guard(self, parser):
        """Test typedef with embedded enum inside include guard (jv.h pattern)."""
        source = '''
#ifndef JV_H
#define JV_H

typedef enum {
    JV_KIND_INVALID,
    JV_KIND_NULL,
    JV_KIND_FALSE,
} jv_kind;

typedef struct {
    unsigned char kind_flags;
} jv;

#endif
'''
        symbols = parser.parse(source)

        names = [s.name for s in symbols]
        assert "jv_kind" in names
        assert "jv" in names
