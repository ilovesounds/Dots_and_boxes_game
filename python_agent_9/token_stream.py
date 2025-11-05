from __future__ import annotations

from collections import deque
from typing import Deque, TextIO


class TokenStream:
    """Utility to read whitespace-delimited tokens from a text stream."""

    def __init__(self, source: TextIO):
        self._source = source
        self._buffer: Deque[str] = deque()

    def next(self) -> str:
        """Return the next token from the stream."""
        while not self._buffer:
            line = self._source.readline()
            if line == "":
                raise EOFError("Unexpected end of input while reading token")
            self._buffer.extend(line.strip().split())
        return self._buffer.popleft()

    def next_int(self) -> int:
        """Read the next token and interpret it as an integer."""
        return int(self.next())

    def next_bool(self) -> bool:
        """Read the next token and interpret it as a boolean."""
        token = self.next()
        lowered = token.lower()
        if lowered in {"true", "false"}:
            return lowered == "true"
        return int(token) != 0
