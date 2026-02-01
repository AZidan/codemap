"""Tests for the C# parser."""

import pytest

# Skip all tests if tree-sitter-c-sharp is not installed
pytest.importorskip("tree_sitter_c_sharp")

from codemap.parsers.csharp_parser import CSharpParser


class TestCSharpParser:
    """Tests for CSharpParser class."""

    @pytest.fixture
    def parser(self):
        return CSharpParser()

    def test_parse_simple_class(self, parser):
        source = '''
public class User
{
    public int Id { get; set; }
    public string Name { get; set; }
}
'''
        symbols = parser.parse(source)

        assert len(symbols) == 1
        assert symbols[0].name == "User"
        assert symbols[0].type == "class"

    def test_parse_class_with_methods(self, parser):
        source = '''
public class Calculator
{
    public int Add(int a, int b)
    {
        return a + b;
    }

    public int Subtract(int a, int b)
    {
        return a - b;
    }
}
'''
        symbols = parser.parse(source)

        assert len(symbols) == 1
        calc = symbols[0]
        assert calc.name == "Calculator"
        assert calc.type == "class"
        assert len(calc.children) == 2
        method_names = [c.name for c in calc.children]
        assert "Add" in method_names
        assert "Subtract" in method_names

    def test_parse_interface(self, parser):
        source = '''
public interface IUserService
{
    User GetUser(int id);
    void CreateUser(string name);
}
'''
        symbols = parser.parse(source)

        assert len(symbols) == 1
        assert symbols[0].name == "IUserService"
        assert symbols[0].type == "interface"

    def test_parse_struct(self, parser):
        source = '''
public struct Point
{
    public int X;
    public int Y;
}
'''
        symbols = parser.parse(source)

        assert len(symbols) == 1
        assert symbols[0].name == "Point"
        assert symbols[0].type == "struct"

    def test_parse_enum(self, parser):
        source = '''
public enum Status
{
    Active,
    Inactive,
    Pending
}
'''
        symbols = parser.parse(source)

        assert len(symbols) == 1
        assert symbols[0].name == "Status"
        assert symbols[0].type == "enum"

    def test_parse_async_method(self, parser):
        source = '''
public class Service
{
    public async Task<User> GetUserAsync(int id)
    {
        await Task.Delay(100);
        return new User();
    }
}
'''
        symbols = parser.parse(source)

        assert len(symbols) == 1
        service = symbols[0]
        assert len(service.children) >= 1
        method = service.children[0]
        assert method.name == "GetUserAsync"
        # Note: async detection depends on parser implementation
        assert method.type in ("method", "async_method")

    def test_parse_constructor(self, parser):
        source = '''
public class User
{
    private string name;

    public User(string name)
    {
        this.name = name;
    }

    public string GetName()
    {
        return name;
    }
}
'''
        symbols = parser.parse(source)

        assert len(symbols) == 1
        user = symbols[0]
        assert user.name == "User"
        method_names = [c.name for c in user.children]
        assert "User" in method_names  # Constructor
        assert "GetName" in method_names

    def test_parse_multiple_classes(self, parser):
        source = '''
class First
{
    void Method1() {}
}

class Second
{
    void Method2() {}
}

class Third
{
    void Method3() {}
}
'''
        symbols = parser.parse(source)

        assert len(symbols) == 3
        names = [s.name for s in symbols]
        assert "First" in names
        assert "Second" in names
        assert "Third" in names

    def test_parse_fixture_file(self, parser):
        """Test parsing the C# fixture file without namespace wrapper."""
        # Test with code that doesn't have a namespace wrapper
        source = '''
public class User
{
    public int Id { get; set; }
    public string Name { get; set; }

    public User(int id, string name)
    {
        Id = id;
        Name = name;
    }
}

public interface IUserService
{
    User GetUser(int id);
}

public enum UserStatus
{
    Active,
    Inactive
}
'''
        symbols = parser.parse(source)

        # Should find multiple symbols
        assert len(symbols) >= 3

        names = [s.name for s in symbols]
        assert "User" in names
        assert "IUserService" in names
        assert "UserStatus" in names

    def test_parse_namespace_wrapped_classes(self, parser):
        """Test that classes inside namespaces are found."""
        source = '''
namespace MyApp.Models
{
    public class User
    {
        public int Id { get; set; }
    }

    public class Order
    {
        public int Total { get; set; }
    }
}
'''
        symbols = parser.parse(source)
        assert len(symbols) == 2
        names = [s.name for s in symbols]
        assert "User" in names
        assert "Order" in names

    def test_parse_file_scoped_namespace(self, parser):
        """Test file-scoped namespace (C# 10+)."""
        source = '''
namespace MyApp.Services;

public class OrderService
{
    public void ProcessOrder(int orderId)
    {
    }
}
'''
        symbols = parser.parse(source)
        assert len(symbols) == 1
        assert symbols[0].name == "OrderService"
        assert len(symbols[0].children) == 1
        assert symbols[0].children[0].name == "ProcessOrder"

    def test_parse_nested_namespaces(self, parser):
        """Test nested namespace declarations."""
        source = '''
namespace Outer
{
    namespace Inner
    {
        public class DeepClass
        {
            public void DeepMethod() {}
        }
    }
}
'''
        symbols = parser.parse(source)
        assert len(symbols) == 1
        assert symbols[0].name == "DeepClass"

    def test_parse_namespace_with_multiple_types(self, parser):
        """Test namespace containing class, interface, enum, and struct."""
        source = '''
namespace MyApp
{
    public class MyClass {}
    public interface IMyInterface {}
    public enum MyEnum { A, B }
    public struct MyStruct {}
}
'''
        symbols = parser.parse(source)
        assert len(symbols) == 4
        types = {s.type for s in symbols}
        assert types == {"class", "interface", "enum", "struct"}
