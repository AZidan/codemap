"""Markdown parser for indexing headers and sections."""

import re
from typing import Optional

from .base import Parser, Symbol


class MarkdownParser(Parser):
    """Parser for Markdown files - indexes H2, H3, and H4 headers."""

    # Match ##, ###, and #### headers
    HEADER_PATTERN = re.compile(r'^(#{2,4})\s+(.+?)\s*$', re.MULTILINE)

    def parse(self, source: str, filepath: Optional[str] = None) -> list[Symbol]:
        """Parse markdown source and extract header symbols.

        Args:
            source: The markdown source code
            filepath: Optional path to the file being parsed

        Returns:
            List of Symbol objects representing headers
        """
        lines = source.split('\n')
        total_lines = len(lines)

        # Find all headers with their positions
        headers: list[tuple[int, int, str, int]] = []  # (level, line_num, title, char_pos)

        for match in self.HEADER_PATTERN.finditer(source):
            hashes = match.group(1)
            title = match.group(2).strip()
            level = len(hashes)  # 2 for ##, 3 for ###

            # Calculate line number from character position
            line_num = source[:match.start()].count('\n') + 1

            headers.append((level, line_num, title, match.start()))

        # Build symbol tree
        symbols: list[Symbol] = []
        h2_stack: list[Symbol] = []  # Track current H2 for nesting H3s
        h3_stack: list[Symbol] = []  # Track current H3 for nesting H4s

        for i, (level, start_line, title, _) in enumerate(headers):
            # Find end line (start of next header at same or higher level, or EOF)
            end_line = total_lines
            for j in range(i + 1, len(headers)):
                next_level, next_line, _, _ = headers[j]
                if next_level <= level:
                    end_line = next_line - 1
                    break

            # Determine symbol type based on header level
            symbol_type = {2: "section", 3: "subsection", 4: "subsubsection"}.get(
                level, "section"
            )

            symbol = Symbol(
                name=title,
                type=symbol_type,
                lines=(start_line, end_line),
                signature=None,
                docstring=self._extract_first_paragraph(lines, start_line, end_line),
                children=[],
            )

            if level == 2:
                # H2: Add to root symbols and track for children
                symbols.append(symbol)
                h2_stack = [symbol]
                h3_stack = []
            elif level == 3:
                if h2_stack:
                    # H3: Add as child of most recent H2
                    h2_stack[-1].children.append(symbol)
                    h3_stack = [symbol]
                else:
                    # Orphan H3 - add to root
                    symbols.append(symbol)
                    h3_stack = [symbol]
            elif level == 4:
                if h3_stack:
                    # H4: Add as child of most recent H3
                    h3_stack[-1].children.append(symbol)
                elif h2_stack:
                    # No H3 parent, add to H2
                    h2_stack[-1].children.append(symbol)
                else:
                    # Orphan H4 - add to root
                    symbols.append(symbol)

        return symbols

    def _extract_first_paragraph(
        self, lines: list[str], start_line: int, end_line: int
    ) -> Optional[str]:
        """Extract first non-empty paragraph after the header."""
        # Start from line after header
        content_lines = []
        in_paragraph = False

        for i in range(start_line, min(end_line, start_line + 10)):
            if i >= len(lines):
                break
            line = lines[i].strip()

            # Skip the header line itself
            if i == start_line - 1:
                continue

            # Skip empty lines before content
            if not line and not in_paragraph:
                continue

            # Stop at empty line after starting paragraph
            if not line and in_paragraph:
                break

            # Skip code blocks, lists, etc.
            if line.startswith('```') or line.startswith('#'):
                break

            in_paragraph = True
            content_lines.append(line)

            # Limit to ~150 chars
            if sum(len(l) for l in content_lines) > 150:
                break

        if content_lines:
            text = ' '.join(content_lines)
            return text[:150] if len(text) > 150 else text
        return None

    @staticmethod
    def supported_extensions() -> list[str]:
        """Return list of supported file extensions."""
        return ['.md', '.markdown']
