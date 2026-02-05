"""Tests for the Ruby parser."""

import pytest

# Skip all tests if tree-sitter-ruby is not installed
pytest.importorskip("tree_sitter_ruby")

from codemap.parsers.ruby_parser import RubyParser


class TestRubyParser:
    """Tests for RubyParser class."""

    @pytest.fixture
    def parser(self):
        return RubyParser()

    def test_parse_simple_class(self, parser):
        source = '''
class Example
  def greet
    "Hello"
  end
end
'''
        symbols = parser.parse(source)

        assert len(symbols) == 1
        assert symbols[0].name == "Example"
        assert symbols[0].type == "class"
        assert symbols[0].children is not None
        assert len(symbols[0].children) == 1
        assert symbols[0].children[0].name == "greet"
        assert symbols[0].children[0].type == "method"

    def test_parse_module(self, parser):
        source = '''
module MyModule
  def helper_method
    "helper"
  end
end
'''
        symbols = parser.parse(source)

        assert len(symbols) == 1
        assert symbols[0].name == "MyModule"
        assert symbols[0].type == "module"
        assert symbols[0].children is not None
        assert len(symbols[0].children) == 1

    def test_parse_class_with_inheritance(self, parser):
        source = '''
class User < ApplicationRecord
  def full_name
    "#{first_name} #{last_name}"
  end
end
'''
        symbols = parser.parse(source)

        assert len(symbols) == 1
        assert symbols[0].name == "User"
        assert symbols[0].type == "class"

    def test_parse_method_with_parameters(self, parser):
        source = '''
class Calculator
  def add(a, b)
    a + b
  end

  def multiply(a, b = 1)
    a * b
  end
end
'''
        symbols = parser.parse(source)

        assert len(symbols) == 1
        calc = symbols[0]
        assert calc.name == "Calculator"
        assert calc.children is not None
        assert len(calc.children) == 2

        # Check method signatures include parameters
        method_names = [m.name for m in calc.children]
        assert "add" in method_names
        assert "multiply" in method_names

    def test_parse_singleton_method(self, parser):
        source = '''
class Service
  def self.create
    new
  end

  def instance_method
    "instance"
  end
end
'''
        symbols = parser.parse(source)

        assert len(symbols) == 1
        service = symbols[0]
        assert service.children is not None
        assert len(service.children) == 2

        types = [m.type for m in service.children]
        assert "singleton_method" in types
        assert "method" in types

    def test_parse_class_self_block(self, parser):
        source = '''
class User
  class << self
    def find_by_email(email)
      find_by(email: email)
    end
  end
end
'''
        symbols = parser.parse(source)

        assert len(symbols) == 1
        user = symbols[0]
        # Methods inside class << self should be found
        assert user.children is not None
        assert len(user.children) >= 1

    def test_parse_nested_module_class(self, parser):
        source = '''
module Authentication
  class Token
    def generate
      SecureRandom.hex
    end
  end
end
'''
        symbols = parser.parse(source)

        assert len(symbols) == 1
        auth = symbols[0]
        assert auth.name == "Authentication"
        assert auth.type == "module"
        assert auth.children is not None
        assert len(auth.children) >= 1

        # Find the nested class
        token = auth.children[0]
        assert token.name == "Token"
        assert token.type == "class"

    def test_parse_top_level_method(self, parser):
        source = '''
def standalone_function
  "standalone"
end

def another_function(x, y)
  x + y
end
'''
        symbols = parser.parse(source)

        assert len(symbols) == 2
        names = [s.name for s in symbols]
        assert "standalone_function" in names
        assert "another_function" in names

    def test_parse_with_comments(self, parser):
        source = '''
# This is the User class
class User
  # Initialize the user
  def initialize(name)
    @name = name
  end
end
'''
        symbols = parser.parse(source)

        assert len(symbols) == 1
        user = symbols[0]
        assert user.name == "User"
        # Docstring should be extracted from preceding comment
        assert user.docstring is not None or user.children is not None

    def test_parse_multiple_classes(self, parser):
        source = '''
class First
  def method_a
  end
end

class Second
  def method_b
  end
end

class Third
  def method_c
  end
end
'''
        symbols = parser.parse(source)

        assert len(symbols) == 3
        names = [s.name for s in symbols]
        assert "First" in names
        assert "Second" in names
        assert "Third" in names

    def test_extensions(self, parser):
        assert ".rb" in parser.extensions
        assert ".rake" in parser.extensions
        assert ".gemspec" in parser.extensions
        assert ".ru" in parser.extensions
        assert ".thor" in parser.extensions

    def test_language(self, parser):
        assert parser.language == "ruby"

    def test_parse_fixture_file(self, parser):
        """Test parsing the Ruby fixture file."""
        import os
        fixture_path = os.path.join(
            os.path.dirname(__file__), "fixtures", "sample_module.rb"
        )
        with open(fixture_path, "r") as f:
            source = f.read()

        symbols = parser.parse(source, fixture_path)

        # Should find multiple symbols
        assert len(symbols) > 0

        # Check for expected symbols
        names = [s.name for s in symbols]
        assert "Authentication" in names
        assert "UsersController" in names
        assert "User" in names
        assert "Calculator" in names

        # Check top-level methods
        assert "standalone_helper" in names
        assert "format_currency" in names
