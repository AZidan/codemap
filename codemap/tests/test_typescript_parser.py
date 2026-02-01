"""Tests for the TypeScript parser."""

import pytest

# Skip all tests if tree-sitter is not available
try:
    from codemap.parsers.typescript_parser import TypeScriptParser, TREE_SITTER_AVAILABLE
except ImportError:
    TREE_SITTER_AVAILABLE = False

pytestmark = pytest.mark.skipif(
    not TREE_SITTER_AVAILABLE,
    reason="tree-sitter-typescript not installed"
)


class TestTypeScriptParser:
    """Tests for TypeScriptParser class."""

    @pytest.fixture
    def parser(self):
        return TypeScriptParser()

    def test_parse_simple_function(self, parser):
        source = '''
function greet(name: string): string {
    return `Hello, ${name}`;
}
'''
        symbols = parser.parse(source, "test.ts")

        assert len(symbols) == 1
        assert symbols[0].name == "greet"
        assert symbols[0].type == "function"
        assert "(name: string)" in symbols[0].signature
        assert ": string" in symbols[0].signature

    def test_parse_async_function(self, parser):
        source = '''
async function fetchData(url: string): Promise<Response> {
    return await fetch(url);
}
'''
        symbols = parser.parse(source, "test.ts")

        assert len(symbols) == 1
        assert symbols[0].name == "fetchData"
        assert symbols[0].type == "async_function"

    def test_parse_arrow_function(self, parser):
        source = '''
const add = (a: number, b: number): number => {
    return a + b;
};
'''
        symbols = parser.parse(source, "test.ts")

        assert len(symbols) == 1
        assert symbols[0].name == "add"
        assert symbols[0].type == "function"
        assert "(a: number, b: number)" in symbols[0].signature

    def test_parse_async_arrow_function(self, parser):
        source = '''
const fetchUser = async (id: number): Promise<User> => {
    return await api.getUser(id);
};
'''
        symbols = parser.parse(source, "test.ts")

        assert len(symbols) == 1
        assert symbols[0].name == "fetchUser"
        assert symbols[0].type == "async_function"

    def test_parse_class_with_methods(self, parser):
        source = '''
class Calculator {
    add(a: number, b: number): number {
        return a + b;
    }

    subtract(a: number, b: number): number {
        return a - b;
    }
}
'''
        symbols = parser.parse(source, "test.ts")

        assert len(symbols) == 1
        calc = symbols[0]
        assert calc.name == "Calculator"
        assert calc.type == "class"
        assert len(calc.children) == 2
        assert calc.children[0].name == "add"
        assert calc.children[0].type == "method"
        assert calc.children[1].name == "subtract"

    def test_parse_class_with_async_method(self, parser):
        source = '''
class Service {
    async fetch(url: string): Promise<any> {
        return await fetch(url);
    }
}
'''
        symbols = parser.parse(source, "test.ts")

        assert len(symbols) == 1
        assert symbols[0].children[0].name == "fetch"
        assert symbols[0].children[0].type == "async_method"

    def test_parse_interface(self, parser):
        source = '''
interface User {
    id: number;
    name: string;
    email?: string;
}
'''
        symbols = parser.parse(source, "test.ts")

        assert len(symbols) == 1
        assert symbols[0].name == "User"
        assert symbols[0].type == "interface"

    def test_parse_type_alias(self, parser):
        source = '''
type Status = "pending" | "active" | "completed";
'''
        symbols = parser.parse(source, "test.ts")

        assert len(symbols) == 1
        assert symbols[0].name == "Status"
        assert symbols[0].type == "type"

    def test_parse_enum(self, parser):
        source = '''
enum Direction {
    Up,
    Down,
    Left,
    Right
}
'''
        symbols = parser.parse(source, "test.ts")

        assert len(symbols) == 1
        assert symbols[0].name == "Direction"
        assert symbols[0].type == "enum"

    def test_parse_exported_function(self, parser):
        source = '''
export function helper(x: number): number {
    return x * 2;
}
'''
        symbols = parser.parse(source, "test.ts")

        assert len(symbols) == 1
        assert symbols[0].name == "helper"
        assert symbols[0].type == "function"

    def test_parse_exported_class(self, parser):
        source = '''
export class Service {
    run(): void {}
}
'''
        symbols = parser.parse(source, "test.ts")

        assert len(symbols) == 1
        assert symbols[0].name == "Service"
        assert symbols[0].type == "class"

    def test_parse_exported_interface(self, parser):
        source = '''
export interface Config {
    apiUrl: string;
    timeout: number;
}
'''
        symbols = parser.parse(source, "test.ts")

        assert len(symbols) == 1
        assert symbols[0].name == "Config"
        assert symbols[0].type == "interface"

    def test_parse_empty_file(self, parser):
        source = ""
        symbols = parser.parse(source, "test.ts")
        assert symbols == []

    def test_parse_multiple_symbols(self, parser):
        source = '''
interface User {
    id: number;
}

class UserService {
    getUser(id: number): User {
        return { id };
    }
}

function createUser(name: string): User {
    return { id: 1 };
}

const deleteUser = (id: number): void => {};
'''
        symbols = parser.parse(source, "test.ts")

        assert len(symbols) == 4
        assert symbols[0].name == "User"
        assert symbols[0].type == "interface"
        assert symbols[1].name == "UserService"
        assert symbols[1].type == "class"
        assert symbols[2].name == "createUser"
        assert symbols[2].type == "function"
        assert symbols[3].name == "deleteUser"
        assert symbols[3].type == "function"

    def test_can_parse_typescript_files(self, parser):
        assert parser.can_parse("test.ts")
        assert parser.can_parse("component.tsx")
        assert parser.can_parse("path/to/file.ts")
        assert not parser.can_parse("script.js")
        assert not parser.can_parse("module.py")

    def test_parse_tsx_file(self, parser):
        source = '''
interface Props {
    name: string;
}

function Greeting({ name }: Props): JSX.Element {
    return <h1>Hello, {name}!</h1>;
}

export default Greeting;
'''
        symbols = parser.parse(source, "component.tsx")

        assert len(symbols) >= 2
        names = [s.name for s in symbols]
        assert "Props" in names
        assert "Greeting" in names

    def test_symbol_to_dict(self, parser):
        source = '''
function example(x: number): string {
    return x.toString();
}
'''
        symbols = parser.parse(source, "test.ts")
        result = symbols[0].to_dict()

        assert result["name"] == "example"
        assert result["type"] == "function"
        assert "lines" in result
        assert "signature" in result

    def test_parse_generic_function(self, parser):
        source = '''
function identity<T>(arg: T): T {
    return arg;
}
'''
        symbols = parser.parse(source, "test.ts")

        assert len(symbols) == 1
        assert symbols[0].name == "identity"
        assert symbols[0].type == "function"

    def test_parse_generic_class(self, parser):
        source = '''
class Container<T> {
    private value: T;

    constructor(value: T) {
        this.value = value;
    }

    getValue(): T {
        return this.value;
    }
}
'''
        symbols = parser.parse(source, "test.ts")

        assert len(symbols) == 1
        assert symbols[0].name == "Container"
        assert symbols[0].type == "class"

    def test_parse_arrow_function_with_type_annotation(self, parser):
        """Arrow function where the variable has a type annotation."""
        source = '''
const validate: Validator = (data) => { return true; };
'''
        symbols = parser.parse(source, "test.ts")
        assert len(symbols) == 1
        assert symbols[0].name == "validate"
        assert symbols[0].type == "function"

    def test_parse_var_arrow_function(self, parser):
        """Arrow function declared with var."""
        source = '''
var oldStyle = (x: number) => x;
'''
        symbols = parser.parse(source, "test.ts")
        assert len(symbols) == 1
        assert symbols[0].name == "oldStyle"
        assert symbols[0].type == "function"

    def test_parse_abstract_class(self, parser):
        """Abstract class with abstract methods."""
        source = '''
abstract class Base {
    abstract compute(): number;
    concrete(): string { return ""; }
}
'''
        symbols = parser.parse(source, "test.ts")
        assert len(symbols) == 1
        cls = symbols[0]
        assert cls.name == "Base"
        assert cls.type == "class"
        assert len(cls.children) == 2
        names = {c.name for c in cls.children}
        assert "compute" in names
        assert "concrete" in names
        for c in cls.children:
            assert c.type == "method"

    def test_parse_class_arrow_property(self, parser):
        """Arrow function assigned to a class property."""
        source = '''
class Handler {
    handle = (event: Event) => { };
    asyncHandle = async (event: Event) => { };
}
'''
        symbols = parser.parse(source, "test.ts")
        assert len(symbols) == 1
        cls = symbols[0]
        assert len(cls.children) == 2
        assert cls.children[0].name == "handle"
        assert cls.children[0].type == "method"
        assert cls.children[1].name == "asyncHandle"
        assert cls.children[1].type == "async_method"

    def test_parse_declare_module(self, parser):
        """Symbols inside declare module blocks."""
        source = '''
declare module 'foo' {
    export function bar(): void;
    export class Baz {}
}
'''
        symbols = parser.parse(source, "test.ts")
        names = {s.name for s in symbols}
        assert "bar" in names
        assert "Baz" in names

    def test_parse_declare_namespace(self, parser):
        """Symbols inside declare namespace blocks."""
        source = '''
declare namespace NS {
    function hello(): void;
    interface Config { key: string; }
}
'''
        symbols = parser.parse(source, "test.ts")
        names = {s.name for s in symbols}
        assert "hello" in names
        assert "Config" in names

    def test_parse_exported_arrow_function(self, parser):
        """Exported arrow function."""
        source = '''
export const transform = async (x: any) => { return x; };
'''
        symbols = parser.parse(source, "test.ts")
        assert len(symbols) == 1
        assert symbols[0].name == "transform"
        assert symbols[0].type == "async_function"
