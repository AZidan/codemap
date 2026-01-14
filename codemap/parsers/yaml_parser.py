"""YAML parser for indexing keys and sections with full hierarchy."""

import re
from typing import Optional

from .base import Parser, Symbol


class YamlParser(Parser):
    """Parser for YAML files - indexes keys recursively with full hierarchy."""

    # Match YAML keys (handles quoted and unquoted keys)
    KEY_PATTERN = re.compile(r'^(\s*)([\w\-_]+|"[^"]+"|\'[^\']+\')\s*:')
    # Match list items that might have nested content
    LIST_ITEM_PATTERN = re.compile(r'^(\s*)-\s+(\w[\w\-_]*)\s*:')

    def parse(self, source: str, filepath: Optional[str] = None) -> list[Symbol]:
        """Parse YAML source and extract key symbols recursively.

        Args:
            source: The YAML source code
            filepath: Optional path to the file being parsed

        Returns:
            List of Symbol objects representing YAML keys/sections
        """
        lines = source.split('\n')
        total_lines = len(lines)

        # Parse all keys with their indentation and line numbers
        keys: list[tuple[int, str, int, bool]] = []  # (indent, name, line_num, is_list_item)

        for line_num, line in enumerate(lines, 1):
            # Skip comments and empty lines
            stripped = line.lstrip()
            if not stripped or stripped.startswith('#'):
                continue

            # Check for list item with key
            list_match = self.LIST_ITEM_PATTERN.match(line)
            if list_match:
                indent = len(list_match.group(1)) + 2  # Account for "- "
                key_name = list_match.group(2)
                keys.append((indent, key_name, line_num, True))
                continue

            # Check for regular key
            key_match = self.KEY_PATTERN.match(line)
            if key_match:
                indent = len(key_match.group(1))
                key_name = key_match.group(2).strip('"\'')
                keys.append((indent, key_name, line_num, False))

        # Build hierarchical symbol tree
        return self._build_hierarchy(keys, lines, total_lines)

    def _build_hierarchy(
        self,
        keys: list[tuple[int, str, int, bool]],
        lines: list[str],
        total_lines: int,
    ) -> list[Symbol]:
        """Build a hierarchical symbol tree from flat key list."""
        if not keys:
            return []

        symbols: list[Symbol] = []
        # Stack of (indent, symbol) for tracking hierarchy
        stack: list[tuple[int, Symbol]] = []

        for i, (indent, name, start_line, is_list_item) in enumerate(keys):
            # Find end line (next key at same or lower indent, or EOF)
            end_line = total_lines
            for j in range(i + 1, len(keys)):
                next_indent, _, next_line, _ = keys[j]
                if next_indent <= indent:
                    end_line = next_line - 1
                    break

            # Determine symbol type
            symbol_type = self._determine_type(lines, start_line, end_line, is_list_item)

            # Extract value preview as docstring
            docstring = self._extract_value_preview(lines, start_line)

            symbol = Symbol(
                name=name,
                type=symbol_type,
                lines=(start_line, end_line),
                signature=None,
                docstring=docstring,
                children=[],
            )

            # Pop stack until we find parent (lower indent)
            while stack and stack[-1][0] >= indent:
                stack.pop()

            if stack:
                # Add as child of parent
                stack[-1][1].children.append(symbol)
            else:
                # Root level symbol
                symbols.append(symbol)

            # Push current symbol to stack
            stack.append((indent, symbol))

        return symbols

    def _determine_type(
        self, lines: list[str], start_line: int, end_line: int, is_list_item: bool
    ) -> str:
        """Determine the type of YAML symbol based on content."""
        if start_line > len(lines):
            return "key"

        line = lines[start_line - 1]

        # Check if it's a list
        if is_list_item:
            return "item"

        # Check what follows the colon
        colon_idx = line.find(':')
        if colon_idx == -1:
            return "key"

        after_colon = line[colon_idx + 1:].strip()

        # Empty after colon = section/mapping
        if not after_colon:
            # Check if children are list items
            if start_line < len(lines):
                next_line = lines[start_line].lstrip()
                if next_line.startswith('-'):
                    return "list"
            return "section"

        # Has inline value
        if after_colon.startswith('[') or after_colon.startswith('{'):
            return "collection"
        if after_colon.startswith('|') or after_colon.startswith('>'):
            return "multiline"

        return "key"

    def _extract_value_preview(self, lines: list[str], line_num: int) -> Optional[str]:
        """Extract a preview of the value for simple key-value pairs."""
        if line_num > len(lines):
            return None

        line = lines[line_num - 1]
        colon_idx = line.find(':')
        if colon_idx == -1:
            return None

        value = line[colon_idx + 1:].strip()

        # Skip if it's a section marker or empty
        if not value or value in ('|', '>', '|-', '>-'):
            return None

        # Return truncated value
        if len(value) > 100:
            return value[:100] + "..."
        return value if value else None

    @staticmethod
    def supported_extensions() -> list[str]:
        """Return list of supported file extensions."""
        return ['.yaml', '.yml']
