# backend/tetris/engine.py
from __future__ import annotations
from dataclasses import dataclass
from typing import List, Optional, Tuple
import random

from .constants import (
    ROWS, COLS,
    GRAVITY_DROP_FRAMES, SOFT_DROP_FRAMES,
    LOCK_DELAY_FRAMES,
    SCORE_SINGLE, SCORE_DOUBLE, SCORE_TRIPLE, SCORE_TETRIS,
    SOFT_DROP_SCORE_PER_CELL, HARD_DROP_SCORE_PER_CELL,
)
from .pieces import TETROMINOES, ActivePiece


def empty_board() -> List[List[int]]:
    return [[0 for _ in range(COLS)] for _ in range(ROWS)]


def new_bag() -> List[int]:
    bag = list(range(7))
    random.shuffle(bag)
    return bag


@dataclass
class GameState:
    board: List[List[int]]
    score: int
    lines: int
    game_over: bool
    
    # RL/event signals (reset every tick)
    just_cleared: int        # how many lines cleared on the most recent lock
    just_locked: bool        # whether a piece locked this tick

    active: ActivePiece
    next_piece_id: int

    # timing state
    frame: int
    lock_timer: int
    soft_drop: bool
    lock_resets_left: int


class TetrisEngine:
    """
    Full-control Tetris simulation:
    - gravity
    - rotate
    - left/right
    - soft drop (down)
    - hard drop (space / "place")
    - lock delay
    - line clears + scoring
    """

    def __init__(self, seed: Optional[int] = None):
        if seed is not None:
            random.seed(seed)

        self._bag: List[int] = new_bag()
        self._bag2: List[int] = new_bag()

        board = empty_board()
        first = self._draw_piece()
        nxt = self._peek_next_piece()

        self.state = GameState(
            board=board,
            score=0,
            lines=0,
            game_over=False,
            
            just_cleared=0,
            just_locked=False,
            
            active=self._spawn(first),
            next_piece_id=nxt,
            frame=0,
            lock_timer=0,
            soft_drop=False,
            lock_resets_left=15,
        )

        # If spawn collides, immediately game over
        if self._collides(self.state.active):
            self.state.game_over = True

    # ---------- piece generation ----------
    def _draw_piece(self) -> int:
        if not self._bag:
            self._bag = self._bag2
            self._bag2 = new_bag()
        return self._bag.pop(0)

    def _peek_next_piece(self) -> int:
        if self._bag:
            return self._bag[0]
        return self._bag2[0]

    def _spawn(self, piece_id: int) -> ActivePiece:
        # Spawn near top middle in a 4x4 box.
        # col = 3 makes room for I piece
        return ActivePiece(piece_id=piece_id, rot=0, row=0, col=3)

    # ---------- collision / placement ----------
    def _in_bounds(self, r: int, c: int) -> bool:
        return 0 <= r < ROWS and 0 <= c < COLS

    def _collides(self, piece: ActivePiece) -> bool:
        for (r, c) in piece.blocks():
            if not self._in_bounds(r, c):
                return True
            if self.state.board[r][c] != 0:
                return True
        return False

    def _lock_piece(self) -> None:
        """Turn active piece into fixed blocks."""
        pid = self.state.active.piece_id
        for (r, c) in self.state.active.blocks():
            if 0 <= r < ROWS and 0 <= c < COLS:
                self.state.board[r][c] = pid + 1  # store color id 1..7

        cleared = self._clear_lines()
        self._score_lines(cleared)
        
        self.state.just_cleared = cleared
        self.state.just_locked = True

        # spawn next
        new_id = self._draw_piece()
        self.state.active = self._spawn(new_id)
        self.state.lock_resets_left = 15
        self.state.next_piece_id = self._peek_next_piece()

        self.state.lock_timer = 0

        if self._collides(self.state.active):
            self.state.game_over = True

    def _clear_lines(self) -> int:
        new_rows = [row for row in self.state.board if any(cell == 0 for cell in row)]
        cleared = ROWS - len(new_rows)
        if cleared > 0:
            for _ in range(cleared):
                new_rows.insert(0, [0 for _ in range(COLS)])
            self.state.board = new_rows
            self.state.lines += cleared
        return cleared

    def _score_lines(self, cleared: int) -> None:
        if cleared == 1:
            self.state.score += SCORE_SINGLE
        elif cleared == 2:
            self.state.score += SCORE_DOUBLE
        elif cleared == 3:
            self.state.score += SCORE_TRIPLE
        elif cleared == 4:
            self.state.score += SCORE_TETRIS

    # ---------- public input actions ----------
    def move_left(self) -> None:
        if self.state.game_over:
            return
        moved = ActivePiece(
            piece_id=self.state.active.piece_id,
            rot=self.state.active.rot,
            row=self.state.active.row,
            col=self.state.active.col - 1,
        )
        if not self._collides(moved):
            self.state.active = moved
            if self._grounded():
                if self.state.lock_resets_left > 0:
                    self.state.lock_resets_left -= 1
                    self.state.lock_timer = 0
            else:
                self.state.lock_timer = 0


    def move_right(self) -> None:
        if self.state.game_over:
            return
        moved = ActivePiece(
            piece_id=self.state.active.piece_id,
            rot=self.state.active.rot,
            row=self.state.active.row,
            col=self.state.active.col + 1,
        )
        if not self._collides(moved):
            self.state.active = moved
            if self._grounded():
                if self.state.lock_resets_left > 0:
                    self.state.lock_resets_left -= 1
                    self.state.lock_timer = 0
            else:
                self.state.lock_timer = 0

    def rotate_cw(self) -> None:
        if self.state.game_over:
            return
        rotated = ActivePiece(
            piece_id=self.state.active.piece_id,
            rot=(self.state.active.rot + 1) % 4,
            row=self.state.active.row,
            col=self.state.active.col,
        )
        # Simple "wall kick": try nudges if collision
        for dx in (0, -1, 1, -2, 2):
            candidate = ActivePiece(
                piece_id=rotated.piece_id,
                rot=rotated.rot,
                row=rotated.row,
                col=rotated.col + dx,
            )
            if not self._collides(candidate):
                self.state.active = candidate
                if self._grounded():
                    if self.state.lock_resets_left > 0:
                        self.state.lock_resets_left -= 1
                        self.state.lock_timer = 0
                else:
                    self.state.lock_timer = 0
                return

    def set_soft_drop(self, enabled: bool) -> None:
        self.state.soft_drop = enabled

    def hard_drop(self) -> None:
        """Drop piece instantly and lock."""
        if self.state.game_over:
            return
        steps = 0
        piece = self.state.active
        while True:
            nxt = ActivePiece(piece_id=piece.piece_id, rot=piece.rot, row=piece.row + 1, col=piece.col)
            if self._collides(nxt):
                break
            piece = nxt
            steps += 1
        self.state.active = piece
        self.state.score += steps * HARD_DROP_SCORE_PER_CELL
        self._lock_piece()
        
    from .pieces import TETROMINOES, ActivePiece  # make sure these imports exist in engine.py

    def hard_drop_from(self, rot: int, target_col: int) -> None:
        """
        Choose a rotation + target origin column, clamp to a valid range for that rotation,
        then hard drop. Guarantees a placement every time.
        """
        if self.state.game_over:
            return

        piece = self.state.active
        rot = rot % 4

        # Determine valid origin-col range for this piece & rotation
        shape = TETROMINOES[piece.piece_id][rot]
        min_c = min(c for _, c in shape)
        max_c = max(c for _, c in shape)

        # origin_col + min_c >= 0  => origin_col >= -min_c
        # origin_col + max_c <= COLS-1 => origin_col <= (COLS-1) - max_c
        min_origin = -min_c
        max_origin = (COLS - 1) - max_c

        # Clamp the requested origin column into valid range
        origin_col = max(min_origin, min(target_col, max_origin))

        # Try to set the rotation at the current row with the clamped origin col
        candidate = ActivePiece(piece_id=piece.piece_id, rot=rot, row=0, col=origin_col)

        # If collision at spawn row (rare), try small kicks
        if self._collides(candidate):
            placed = None
            for dx in (0, -1, 1, -2, 2):
                cand2 = ActivePiece(piece_id=piece.piece_id, rot=rot, row=0, col=origin_col + dx)
                if not self._collides(cand2):
                    placed = cand2
                    break
            if placed is None:
                # Fallback: hard drop as-is
                self.hard_drop()
                return
            candidate = placed

        self.state.active = candidate
        self.hard_drop()


    # ---------- ticking / gravity ----------
    def _try_fall_one(self) -> bool:
        """Return True if fell, False if blocked."""
        piece = self.state.active
        nxt = ActivePiece(piece_id=piece.piece_id, rot=piece.rot, row=piece.row + 1, col=piece.col)
        if self._collides(nxt):
            return False
        self.state.active = nxt
        return True
    
    def _can_fall(self) -> bool:
        piece = self.state.active
        nxt = ActivePiece(piece_id=piece.piece_id, rot=piece.rot, row=piece.row + 1, col=piece.col)
        return not self._collides(nxt)
    
    def _grounded(self) -> bool:
        return not self._can_fall()



    def tick(self) -> None:
        """
        Advance time by 1 frame.
        Gravity:
          - every GRAVITY_DROP_FRAMES frames, fall 1 cell
          - if soft drop held, fall every SOFT_DROP_FRAMES frames
        Lock delay:
          - when blocked, start lock_timer
          - if lock_timer reaches LOCK_DELAY_FRAMES, lock piece
        """
        if self.state.game_over:
            return

        # reset one-tick signals
        self.state.just_cleared = 0
        self.state.just_locked = False

        self.state.frame += 1
        drop_frames = SOFT_DROP_FRAMES if self.state.soft_drop else GRAVITY_DROP_FRAMES

        # If we're NOT on a gravity step, we still need to handle lock delay
        # when the piece is already on the ground.
        if self.state.frame % drop_frames != 0:
            # Check if piece is grounded (can't fall). If grounded, count lock delay in real frames.
            if not self._can_fall():
                self.state.lock_timer += 1
                if self.state.lock_timer >= LOCK_DELAY_FRAMES:
                    self._lock_piece()
            return

        # On gravity step: try to fall
        fell = self._try_fall_one()
        if fell:
            if self.state.soft_drop:
                self.state.score += SOFT_DROP_SCORE_PER_CELL
            self.state.lock_timer = 0
            return

        # blocked on gravity step: grounded, count lock delay
        self.state.lock_timer += 1
        if self.state.lock_timer >= LOCK_DELAY_FRAMES:
            self._lock_piece()

    # ---------- state for UI ----------
    def to_render_board(self) -> List[List[int]]:
        """
        Return a board with the active piece drawn on top.
        Fixed blocks are 1..7, empty is 0.
        Active piece also uses 1..7 (piece_id+1).
        """
        b = [row[:] for row in self.state.board]
        pid_color = self.state.active.piece_id + 1
        for (r, c) in self.state.active.blocks():
            if 0 <= r < ROWS and 0 <= c < COLS:
                b[r][c] = pid_color
        return b
