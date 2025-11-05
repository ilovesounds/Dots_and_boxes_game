from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Move:
    """Represents a single line placement on the dots board."""

    row: int
    col: int
    is_horizontal: bool

    def to_protocol(self) -> str:
        """Return the move encoded in the engine protocol format."""
        return f"{self.row} {self.col} {1 if self.is_horizontal else 0}"

    @classmethod
    def from_token_stream(cls, tokens: "TokenStream") -> "Move":
        """Create a move by consuming three tokens from *tokens*."""
        row = tokens.next_int()
        col = tokens.next_int()
        is_horizontal = tokens.next_bool()
        return cls(row=row, col=col, is_horizontal=is_horizontal)


# Late import to avoid a circular dependency during type checking.
from typing import TYPE_CHECKING

if TYPE_CHECKING:  # pragma: no cover
    from .token_stream import TokenStream
