# backend/tetris/pieces.py
from __future__ import annotations
from dataclasses import dataclass
from typing import List, Tuple, Dict

# Coordinates are (row, col) within a 4x4 bounding box.
# We'll rotate by using pre-defined rotations for simplicity and correctness.

# Each piece: list of 4 rotations.
# Each rotation: list of (r, c) blocks (4 blocks per piece).
TETROMINOES: Dict[int, List[List[Tuple[int, int]]]] = {
    # 0: I
    0: [
        [(1, 0), (1, 1), (1, 2), (1, 3)],
        [(0, 2), (1, 2), (2, 2), (3, 2)],
        [(2, 0), (2, 1), (2, 2), (2, 3)],
        [(0, 1), (1, 1), (2, 1), (3, 1)],
    ],
    # 1: J
    1: [
        [(0, 0), (1, 0), (1, 1), (1, 2)],
        [(0, 1), (0, 2), (1, 1), (2, 1)],
        [(1, 0), (1, 1), (1, 2), (2, 2)],
        [(0, 1), (1, 1), (2, 0), (2, 1)],
    ],
    # 2: L
    2: [
        [(0, 2), (1, 0), (1, 1), (1, 2)],
        [(0, 1), (1, 1), (2, 1), (2, 2)],
        [(1, 0), (1, 1), (1, 2), (2, 0)],
        [(0, 0), (0, 1), (1, 1), (2, 1)],
    ],
    # 3: O
    3: [
        [(0, 1), (0, 2), (1, 1), (1, 2)],
        [(0, 1), (0, 2), (1, 1), (1, 2)],
        [(0, 1), (0, 2), (1, 1), (1, 2)],
        [(0, 1), (0, 2), (1, 1), (1, 2)],
    ],
    # 4: S
    4: [
        [(0, 1), (0, 2), (1, 0), (1, 1)],
        [(0, 1), (1, 1), (1, 2), (2, 2)],
        [(1, 1), (1, 2), (2, 0), (2, 1)],
        [(0, 0), (1, 0), (1, 1), (2, 1)],
    ],
    # 5: Z
    5: [
        [(0, 0), (0, 1), (1, 1), (1, 2)],
        [(0, 2), (1, 1), (1, 2), (2, 1)],
        [(1, 0), (1, 1), (2, 1), (2, 2)],
        [(0, 1), (1, 0), (1, 1), (2, 0)],
    ],
    # 6: T
    6: [
        [(0, 1), (1, 0), (1, 1), (1, 2)],
        [(0, 1), (1, 1), (1, 2), (2, 1)],
        [(1, 0), (1, 1), (1, 2), (2, 1)],
        [(0, 1), (1, 0), (1, 1), (2, 1)],
    ],
}


@dataclass(frozen=True)
class ActivePiece:
    piece_id: int          # 0..6
    rot: int               # 0..3
    row: int               # top-left origin of the 4x4 box
    col: int               # top-left origin of the 4x4 box

    def blocks(self) -> List[Tuple[int, int]]:
        """Absolute (row, col) of the 4 blocks on the board."""
        shape = TETROMINOES[self.piece_id][self.rot]
        return [(self.row + r, self.col + c) for (r, c) in shape]
