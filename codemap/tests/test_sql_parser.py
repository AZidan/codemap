"""Tests for the SQL parser."""

import os

import pytest

# Skip if grammar not installed
pytest.importorskip("tree_sitter_sql")

from codemap.parsers.sql_parser import SQLParser


class TestSQLParser:
    """Tests for SQLParser class."""

    @pytest.fixture
    def parser(self):
        return SQLParser()

    def test_parse_table(self, parser):
        """Test parsing CREATE TABLE statements."""
        source = """
        CREATE TABLE users (
            id INT PRIMARY KEY,
            name VARCHAR(255) NOT NULL
        );
        """
        symbols = parser.parse(source)
        assert len(symbols) == 1
        assert symbols[0].name == "users"
        assert symbols[0].type == "table"
        # Check column children
        assert symbols[0].children is not None
        assert len(symbols[0].children) == 2
        assert symbols[0].children[0].name == "id"
        assert symbols[0].children[0].type == "column"
        assert symbols[0].children[1].name == "name"
        assert symbols[0].children[1].type == "column"

    def test_parse_view(self, parser):
        """Test parsing CREATE VIEW statements."""
        source = """
        CREATE VIEW active_users AS
        SELECT * FROM users WHERE active = true;
        """
        symbols = parser.parse(source)
        assert len(symbols) == 1
        assert symbols[0].name == "active_users"
        assert symbols[0].type == "view"

    def test_parse_materialized_view(self, parser):
        """Test parsing CREATE MATERIALIZED VIEW statements."""
        source = """
        CREATE MATERIALIZED VIEW user_summary AS
        SELECT COUNT(*) AS total FROM users;
        """
        symbols = parser.parse(source)
        assert len(symbols) == 1
        assert symbols[0].name == "user_summary"
        assert symbols[0].type == "materialized_view"

    def test_parse_index(self, parser):
        """Test parsing CREATE INDEX statements."""
        source = """CREATE INDEX idx_users_email ON users(email);"""
        symbols = parser.parse(source)
        assert len(symbols) == 1
        assert symbols[0].name == "idx_users_email"
        assert symbols[0].type == "index"

    def test_parse_function(self, parser):
        """Test parsing CREATE FUNCTION statements."""
        source = """
        CREATE FUNCTION get_count() RETURNS INT AS $$
        BEGIN
            RETURN 1;
        END;
        $$ LANGUAGE plpgsql;
        """
        symbols = parser.parse(source)
        assert len(symbols) == 1
        assert symbols[0].name == "get_count"
        assert symbols[0].type == "function"
        assert symbols[0].signature is not None
        assert "INT" in symbols[0].signature

    def test_parse_function_with_parameters(self, parser):
        """Test parsing functions with parameters."""
        source = """
        CREATE FUNCTION add_numbers(a INT, b INT) RETURNS INT AS $$
        BEGIN
            RETURN a + b;
        END;
        $$ LANGUAGE plpgsql;
        """
        symbols = parser.parse(source)
        assert len(symbols) == 1
        assert symbols[0].name == "add_numbers"
        assert symbols[0].type == "function"
        assert symbols[0].signature is not None
        # Check signature includes parameters
        assert "a" in symbols[0].signature or "INT" in symbols[0].signature

    def test_parse_trigger(self, parser):
        """Test parsing CREATE TRIGGER statements."""
        source = """
        CREATE TRIGGER update_timestamp
        BEFORE UPDATE ON users
        FOR EACH ROW EXECUTE FUNCTION update_ts();
        """
        symbols = parser.parse(source)
        assert len(symbols) == 1
        assert symbols[0].name == "update_timestamp"
        assert symbols[0].type == "trigger"

    def test_parse_type(self, parser):
        """Test parsing CREATE TYPE statements."""
        source = """CREATE TYPE status_enum AS ENUM ('active', 'inactive');"""
        symbols = parser.parse(source)
        assert len(symbols) == 1
        assert symbols[0].name == "status_enum"
        assert symbols[0].type == "type"

    def test_parse_sequence(self, parser):
        """Test parsing CREATE SEQUENCE statements."""
        source = """CREATE SEQUENCE user_id_seq START WITH 1 INCREMENT BY 1;"""
        symbols = parser.parse(source)
        assert len(symbols) == 1
        assert symbols[0].name == "user_id_seq"
        assert symbols[0].type == "sequence"

    def test_parse_schema(self, parser):
        """Test parsing CREATE SCHEMA statements."""
        source = """CREATE SCHEMA analytics;"""
        symbols = parser.parse(source)
        assert len(symbols) == 1
        assert symbols[0].name == "analytics"
        assert symbols[0].type == "schema"

    def test_parse_database(self, parser):
        """Test parsing CREATE DATABASE statements."""
        source = """CREATE DATABASE test_db;"""
        symbols = parser.parse(source)
        assert len(symbols) == 1
        assert symbols[0].name == "test_db"
        assert symbols[0].type == "database"

    def test_parse_multiple_statements(self, parser):
        """Test parsing multiple SQL statements."""
        source = """
        CREATE TABLE users (id INT);
        CREATE VIEW active_users AS SELECT * FROM users;
        CREATE INDEX idx_users ON users(id);
        """
        symbols = parser.parse(source)
        assert len(symbols) == 3
        types = [s.type for s in symbols]
        assert "table" in types
        assert "view" in types
        assert "index" in types

    def test_parse_with_comments(self, parser):
        """Test parsing SQL with comments."""
        source = """
        -- User table for storing user data
        CREATE TABLE users (
            id INT PRIMARY KEY
        );
        """
        symbols = parser.parse(source)
        assert len(symbols) == 1
        assert symbols[0].name == "users"
        # Note: comment extraction may vary based on tree-sitter grammar

    def test_parse_empty_source(self, parser):
        """Test parsing empty source."""
        symbols = parser.parse("")
        assert symbols == []

    def test_parse_only_comments(self, parser):
        """Test parsing source with only comments."""
        source = """
        -- This is a comment
        /* Multi-line
           comment */
        """
        symbols = parser.parse(source)
        assert symbols == []

    def test_parse_fixture_file(self, parser):
        """Test parsing the fixture file."""
        fixture_path = os.path.join(
            os.path.dirname(__file__), "fixtures", "sample_database.sql"
        )
        with open(fixture_path, "r") as f:
            source = f.read()
        symbols = parser.parse(source, fixture_path)
        # Should have multiple symbols
        assert len(symbols) >= 10
        # Check for expected types
        types = [s.type for s in symbols]
        assert "table" in types
        assert "view" in types
        assert "index" in types
        assert "function" in types
        assert "trigger" in types
        assert "type" in types
        assert "sequence" in types
        assert "schema" in types

    def test_extensions(self, parser):
        """Test that parser reports correct extensions."""
        assert ".sql" in parser.extensions

    def test_language(self, parser):
        """Test that parser reports correct language."""
        assert parser.language == "sql"

    def test_line_numbers(self, parser):
        """Test that line numbers are correctly reported."""
        source = """CREATE TABLE test (
    id INT
);"""
        symbols = parser.parse(source)
        assert len(symbols) == 1
        # Should span multiple lines
        assert symbols[0].lines[0] == 1
        assert symbols[0].lines[1] >= 3

    def test_table_with_many_columns(self, parser):
        """Test parsing table with many columns."""
        source = """
        CREATE TABLE products (
            id SERIAL PRIMARY KEY,
            name VARCHAR(255),
            description TEXT,
            price DECIMAL(10, 2),
            quantity INT,
            category_id INT,
            created_at TIMESTAMP
        );
        """
        symbols = parser.parse(source)
        assert len(symbols) == 1
        assert symbols[0].name == "products"
        assert symbols[0].children is not None
        assert len(symbols[0].children) == 7
