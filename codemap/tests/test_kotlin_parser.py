"""Tests for the Kotlin parser."""

import pytest

# Skip all tests if tree-sitter-kotlin is not installed
pytest.importorskip("tree_sitter_kotlin")

from codemap.parsers.kotlin_parser import KotlinParser


class TestKotlinParser:
    """Tests for KotlinParser class."""

    @pytest.fixture
    def parser(self):
        return KotlinParser()

    def test_parse_simple_class(self, parser):
        source = '''
class User {
    val id: Int = 0
    val name: String = ""
}
'''
        symbols = parser.parse(source)

        assert len(symbols) == 1
        assert symbols[0].name == "User"
        assert symbols[0].type == "class"

    def test_parse_data_class(self, parser):
        source = '''
data class User(
    val id: Int,
    val name: String
)
'''
        symbols = parser.parse(source)

        assert len(symbols) == 1
        assert symbols[0].name == "User"
        assert symbols[0].type == "class"

    def test_parse_class_with_methods(self, parser):
        source = '''
class Calculator {
    fun add(a: Int, b: Int): Int {
        return a + b
    }

    fun subtract(a: Int, b: Int): Int {
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

    def test_parse_interface(self, parser):
        source = '''
interface UserService {
    fun getUser(id: Int): User?
    fun createUser(name: String): User
}
'''
        symbols = parser.parse(source)

        assert len(symbols) == 1
        assert symbols[0].name == "UserService"
        assert symbols[0].type == "interface"

    def test_parse_object_declaration(self, parser):
        source = '''
object AppConfig {
    val version = "1.0.0"

    fun getConfigString(): String {
        return "App v$version"
    }
}
'''
        symbols = parser.parse(source)

        assert len(symbols) == 1
        assert symbols[0].name == "AppConfig"
        assert symbols[0].type == "class"

    def test_parse_top_level_function(self, parser):
        source = '''
fun validateEmail(email: String): Boolean {
    return email.contains("@")
}

fun formatName(name: String): String {
    return name.trim()
}
'''
        symbols = parser.parse(source)

        assert len(symbols) == 2
        assert symbols[0].name == "validateEmail"
        assert symbols[0].type == "function"
        assert symbols[1].name == "formatName"
        assert symbols[1].type == "function"

    def test_parse_multiple_classes(self, parser):
        source = '''
class First {
    fun method1() {}
}

class Second {
    fun method2() {}
}

class Third {
    fun method3() {}
}
'''
        symbols = parser.parse(source)

        assert len(symbols) == 3
        names = [s.name for s in symbols]
        assert "First" in names
        assert "Second" in names
        assert "Third" in names

    def test_parse_fixture_file(self, parser):
        """Test parsing the Kotlin fixture file."""
        import os
        fixture_path = os.path.join(
            os.path.dirname(__file__), "fixtures", "SampleModule.kt"
        )
        with open(fixture_path, "r") as f:
            source = f.read()

        symbols = parser.parse(source, fixture_path)

        # Should find multiple symbols (classes, interfaces, objects, functions)
        assert len(symbols) >= 4

        names = [s.name for s in symbols]
        assert "User" in names
        assert "UserService" in names
        assert "DefaultUserService" in names

    def test_extensions(self, parser):
        """Test that the parser handles the correct extensions."""
        assert ".kt" in parser.extensions
        assert ".kts" in parser.extensions

    def test_language(self, parser):
        """Test that the parser reports the correct language."""
        assert parser.language == "kotlin"
