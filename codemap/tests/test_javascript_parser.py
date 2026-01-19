"""Tests for the JavaScript parser."""

import pytest

# Skip all tests if tree-sitter is not available
try:
    from codemap.parsers.javascript_parser import JavaScriptParser, TREE_SITTER_AVAILABLE
except ImportError:
    TREE_SITTER_AVAILABLE = False

pytestmark = pytest.mark.skipif(
    not TREE_SITTER_AVAILABLE,
    reason="tree-sitter-javascript not installed"
)


class TestJavaScriptParser:
    """Tests for JavaScriptParser class."""

    @pytest.fixture
    def parser(self):
        return JavaScriptParser()

    def test_parse_simple_function(self, parser):
        source = '''
function greet(name) {
    return `Hello, ${name}`;
}
'''
        symbols = parser.parse(source, "test.js")

        assert len(symbols) == 1
        assert symbols[0].name == "greet"
        assert symbols[0].type == "function"
        assert "(name)" in symbols[0].signature

    def test_parse_async_function(self, parser):
        source = '''
async function fetchData(url) {
    return await fetch(url);
}
'''
        symbols = parser.parse(source, "test.js")

        assert len(symbols) == 1
        assert symbols[0].name == "fetchData"
        assert symbols[0].type == "async_function"

    def test_parse_arrow_function(self, parser):
        source = '''
const add = (a, b) => {
    return a + b;
};
'''
        symbols = parser.parse(source, "test.js")

        assert len(symbols) == 1
        assert symbols[0].name == "add"
        assert symbols[0].type == "function"
        assert "(a, b)" in symbols[0].signature

    def test_parse_arrow_function_implicit_return(self, parser):
        source = '''
const double = x => x * 2;
'''
        symbols = parser.parse(source, "test.js")

        assert len(symbols) == 1
        assert symbols[0].name == "double"
        assert symbols[0].type == "function"

    def test_parse_async_arrow_function(self, parser):
        source = '''
const fetchUser = async (id) => {
    return await api.getUser(id);
};
'''
        symbols = parser.parse(source, "test.js")

        assert len(symbols) == 1
        assert symbols[0].name == "fetchUser"
        assert symbols[0].type == "async_function"

    def test_parse_class_with_methods(self, parser):
        source = '''
class Calculator {
    add(a, b) {
        return a + b;
    }

    subtract(a, b) {
        return a - b;
    }
}
'''
        symbols = parser.parse(source, "test.js")

        assert len(symbols) == 1
        calc = symbols[0]
        assert calc.name == "Calculator"
        assert calc.type == "class"
        assert len(calc.children) == 2
        assert calc.children[0].name == "add"
        assert calc.children[0].type == "method"
        assert calc.children[1].name == "subtract"

    def test_parse_class_with_constructor(self, parser):
        source = '''
class Person {
    constructor(name) {
        this.name = name;
    }

    greet() {
        return `Hello, ${this.name}`;
    }
}
'''
        symbols = parser.parse(source, "test.js")

        assert len(symbols) == 1
        person = symbols[0]
        assert person.name == "Person"
        method_names = [m.name for m in person.children]
        assert "constructor" in method_names
        assert "greet" in method_names

    def test_parse_class_with_async_method(self, parser):
        source = '''
class Service {
    async fetch(url) {
        return await fetch(url);
    }
}
'''
        symbols = parser.parse(source, "test.js")

        assert len(symbols) == 1
        assert symbols[0].children[0].name == "fetch"
        assert symbols[0].children[0].type == "async_method"

    def test_parse_exported_function(self, parser):
        source = '''
export function helper(x) {
    return x * 2;
}
'''
        symbols = parser.parse(source, "test.js")

        assert len(symbols) == 1
        assert symbols[0].name == "helper"
        assert symbols[0].type == "function"

    def test_parse_exported_class(self, parser):
        source = '''
export class Service {
    run() {}
}
'''
        symbols = parser.parse(source, "test.js")

        assert len(symbols) == 1
        assert symbols[0].name == "Service"
        assert symbols[0].type == "class"

    def test_parse_default_export_class(self, parser):
        source = '''
export default class Service {
    run() {}
}
'''
        symbols = parser.parse(source, "test.js")

        assert len(symbols) == 1
        assert symbols[0].name == "Service"
        assert symbols[0].type == "class"

    def test_parse_empty_file(self, parser):
        source = ""
        symbols = parser.parse(source, "test.js")
        assert symbols == []

    def test_parse_multiple_symbols(self, parser):
        source = '''
class UserService {
    getUser(id) {
        return { id };
    }
}

function createUser(name) {
    return { id: 1, name };
}

const deleteUser = (id) => {
    console.log('Deleted', id);
};
'''
        symbols = parser.parse(source, "test.js")

        assert len(symbols) == 3
        assert symbols[0].name == "UserService"
        assert symbols[0].type == "class"
        assert symbols[1].name == "createUser"
        assert symbols[1].type == "function"
        assert symbols[2].name == "deleteUser"
        assert symbols[2].type == "function"

    def test_can_parse_javascript_files(self, parser):
        assert parser.can_parse("test.js")
        assert parser.can_parse("component.jsx")
        assert parser.can_parse("module.mjs")
        assert parser.can_parse("config.cjs")
        assert not parser.can_parse("script.ts")
        assert not parser.can_parse("module.py")

    def test_symbol_to_dict(self, parser):
        source = '''
function example(x) {
    return x.toString();
}
'''
        symbols = parser.parse(source, "test.js")
        result = symbols[0].to_dict()

        assert result["name"] == "example"
        assert result["type"] == "function"
        assert "lines" in result
        assert "signature" in result

    def test_parse_var_function(self, parser):
        source = '''
var oldStyle = function(x) {
    return x * 2;
};
'''
        symbols = parser.parse(source, "test.js")

        assert len(symbols) == 1
        assert symbols[0].name == "oldStyle"
        assert symbols[0].type == "function"

    def test_parse_let_arrow_function(self, parser):
        source = '''
let mutable = (x) => x + 1;
'''
        symbols = parser.parse(source, "test.js")

        assert len(symbols) == 1
        assert symbols[0].name == "mutable"
        assert symbols[0].type == "function"

    def test_parse_with_jsdoc(self, parser):
        source = '''
/**
 * Adds two numbers together.
 * @param {number} a - First number
 * @param {number} b - Second number
 * @returns {number} The sum
 */
function add(a, b) {
    return a + b;
}
'''
        symbols = parser.parse(source, "test.js")

        assert len(symbols) == 1
        assert symbols[0].name == "add"
        # JSDoc should be captured
        if symbols[0].docstring:
            assert "Adds two numbers" in symbols[0].docstring

    def test_commonjs_named_function_expression(self, parser):
        """Test CommonJS pattern: obj.method = function name() {}"""
        source = '''
app.handle = function handle(req, res) {
    console.log('test');
};
'''
        symbols = parser.parse(source, "test.js")

        assert len(symbols) == 1
        assert symbols[0].name == "handle"
        assert symbols[0].type == "function"
        assert "(req, res)" in symbols[0].signature

    def test_commonjs_arrow_function(self, parser):
        """Test CommonJS pattern: obj.method = () => {}"""
        source = '''
app.middleware = (req, res, next) => {
    next();
};
'''
        symbols = parser.parse(source, "test.js")

        assert len(symbols) == 1
        assert symbols[0].name == "middleware"
        assert symbols[0].type == "function"
        assert "(req, res, next)" in symbols[0].signature

    def test_commonjs_async_function(self, parser):
        """Test CommonJS pattern: obj.method = async function name() {}"""
        source = '''
app.fetch = async function fetch(url) {
    return await fetch(url);
};
'''
        symbols = parser.parse(source, "test.js")

        assert len(symbols) == 1
        assert symbols[0].name == "fetch"
        assert symbols[0].type == "async_function"

    def test_commonjs_module_exports(self, parser):
        """Test CommonJS pattern: module.exports.name = function() {}"""
        source = '''
module.exports.helper = function helper(data) {
    return data;
};
'''
        symbols = parser.parse(source, "test.js")

        assert len(symbols) == 1
        assert symbols[0].name == "helper"
        assert symbols[0].type == "function"

    def test_commonjs_prototype_assignment(self, parser):
        """Test CommonJS pattern: Constructor.prototype.method = function() {}"""
        source = '''
Response.prototype.send = function send(body) {
    return body;
};
'''
        symbols = parser.parse(source, "test.js")

        assert len(symbols) == 1
        assert symbols[0].name == "send"
        assert symbols[0].type == "function"

    def test_commonjs_anonymous_function_uses_property_name(self, parser):
        """Test that anonymous functions use the property name for indexing."""
        source = '''
app.anon = function() {
    return null;
};
'''
        symbols = parser.parse(source, "test.js")

        # Anonymous function uses property name from member expression
        assert len(symbols) == 1
        assert symbols[0].name == "anon"
        assert symbols[0].type == "function"

    def test_commonjs_multiple_patterns(self, parser):
        """Test parsing multiple CommonJS patterns in one file."""
        source = '''
app.handle = function handle(req, res) {
    console.log('test');
};

res.json = function json(obj) {
    return obj;
};

app.middleware = (req, res, next) => {
    next();
};

app.fetch = async function fetch(url) {
    return await fetch(url);
};
'''
        symbols = parser.parse(source, "test.js")

        assert len(symbols) == 4
        names = [s.name for s in symbols]
        assert "handle" in names
        assert "json" in names
        assert "middleware" in names
        assert "fetch" in names

        # Verify async detection
        fetch_symbol = next(s for s in symbols if s.name == "fetch")
        assert fetch_symbol.type == "async_function"
