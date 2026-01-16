import numpy as np
import gymnasium as gym
from gymnasium import spaces

from tetris.engine import TetrisEngine
from tetris.constants import ROWS, COLS, GRAVITY_FPS

def column_heights(board):
    # board is 20x10 with 0 empty, >0 filled
    heights = []
    rows = len(board)
    cols = len(board[0])
    for c in range(cols):
        h = 0
        for r in range(rows):
            if board[r][c] != 0:
                h = rows - r
                break
        heights.append(h)
    return heights

def count_holes(board):
    rows = len(board)
    cols = len(board[0])
    holes = 0
    for c in range(cols):
        found_block = False
        for r in range(rows):
            if board[r][c] != 0:
                found_block = True
            elif found_block and board[r][c] == 0:
                holes += 1
    return holes

def bumpiness(heights):
    return sum(abs(heights[i] - heights[i+1]) for i in range(len(heights)-1))

def locked_grid(engine):
    # engine.state.grid is the settled board (no active piece)
    return engine.state.grid

def piece_mask_4x4(piece_id: int, rot: int):
    # 16-length 0/1 vector
    from tetris.pieces import TETROMINOES
    mask = np.zeros((4, 4), dtype=np.float32)
    for r, c in TETROMINOES[piece_id][rot % 4]:
        mask[r][c] = 1.0
    return mask.flatten()



class TetrisRLEnv(gym.Env):
    """
    Gymnasium environment wrapping our TetrisEngine.
    One env step = apply action once, then advance a small time window.
    """

    metadata = {"render_modes": []}

    def __init__(self, frames_per_step: int = 6):
        super().__init__()
        self.frames_per_step = frames_per_step
        self.engine = TetrisEngine()

        # actions: 0..39 → index into valid placements list
        self.action_space = spaces.Discrete(40)

        # observation:
        # 200 cells + 2 ids + 10 heights + holes + bumpiness = 214
        self.observation_space = spaces.Box(
            low=0.0,
            high=1.0,
            shape=(ROWS * COLS + 2 + 10 + 2 + 32,),
            dtype=np.float32
        )


    def _valid_actions(self):
        """
        Returns a list of (rot, col) placements that are valid for the current piece
        when dropped.
        """
        placements = []
        piece_id = self.engine.state.active.piece_id

        for rot in range(4):
            # try all origin columns 0..COLS-1, engine will clamp/correct later
            for col in range(COLS):
                # Clone engine shallowly by making a fresh engine and copying state is hard,
                # so instead we do a safe "try" using collision checks:
                # We simulate the piece at (row=0, col=col) and see if any position is possible.
                # We'll rely on engine's internal collision check by constructing ActivePiece.
                from tetris.pieces import ActivePiece, TETROMINOES
                shape = TETROMINOES[piece_id][rot]

                # compute min/max occupied cols within 4x4
                min_c = min(c for _, c in shape)
                max_c = max(c for _, c in shape)
                min_origin = -min_c
                max_origin = (COLS - 1) - max_c

                if col < min_origin or col > max_origin:
                    continue

                test_piece = ActivePiece(piece_id=piece_id, rot=rot, row=self.engine.state.active.row, col=col)
                if not self.engine._collides(test_piece):  # uses engine collision
                    placements.append((rot, col))

        if not placements:
            placements.append((self.engine.state.active.rot, self.engine.state.active.col))
        return placements



    def _obs(self):
        board = self.engine.to_render_board()

        # binary occupancy
        flat = np.array(board, dtype=np.int8)
        flat = (flat > 0).astype(np.float32).flatten()

        # piece ids normalized 0..1
        cur_id = np.array([self.engine.state.active.piece_id / 6.0], dtype=np.float32)
        nxt_id = np.array([self.engine.state.next_piece_id / 6.0], dtype=np.float32)
        cur_mask = piece_mask_4x4(self.engine.state.active.piece_id, self.engine.state.active.rot)
        nxt_mask = piece_mask_4x4(self.engine.state.next_piece_id, 0)  # rot unknown; use canonical


        # features normalized
        heights = column_heights(board)  # 0..20
        heights_norm = np.array([h / ROWS for h in heights], dtype=np.float32)

        holes = count_holes(board)  # 0..(roughly 200)
        holes_norm = np.array([min(holes, 200) / 200.0], dtype=np.float32)

        bump = bumpiness(heights)  # 0..(20*9=180)
        bump_norm = np.array([min(bump, 180) / 180.0], dtype=np.float32)

        obs = np.concatenate([
            flat,
            cur_id, nxt_id,
            cur_mask, nxt_mask,
            heights_norm, holes_norm, bump_norm
        ]).astype(np.float32)
        return obs

    def reset(self, seed=None, options=None):
        super().reset(seed=seed)
        self.engine = TetrisEngine()
        return self._obs(), {}

    def step(self, action):
        # --- measure BEFORE (LOCKED board only; excludes falling piece) ---
        board_before = self.engine.state.board
        holes_before = count_holes(board_before)
        heights_before = column_heights(board_before)
        maxh_before = max(heights_before) if heights_before else 0
        lines_before = self.engine.state.lines

        # --- decode action 0..39 -> (rot, col) ---
        rot = int(action) // 10   # 0..3
        col = int(action) % 10    # 0..9

        # --- apply placement ---
        self.engine.hard_drop_from(rot, col)

        # advance a tiny bit so next piece spawns cleanly
        for _ in range(2):
            self.engine.tick()
            if self.engine.state.game_over:
                break

        # --- measure AFTER (LOCKED board only) ---
        board_after = self.engine.state.board
        holes_after = count_holes(board_after)
        heights_after = column_heights(board_after)
        bump_after = bumpiness(heights_after)
        maxh_after = max(heights_after) if heights_after else 0
        lines_after = self.engine.state.lines

        cleared = lines_after - lines_before

       # --- reward shaping (phase 2: quality) ---
        reward = 0.0
        reward += 0.2                # survival bonus
        
        # multi-line clear bonus
        if cleared == 1:
            reward += 8.0
        elif cleared == 2:
            reward += 18.0
        elif cleared == 3:
            reward += 30.0
        elif cleared >= 4:
            reward += 45.0     

        # gentle quality shaping 
        reward -= holes_after * 0.02
        reward -= maxh_after * 0.01
        reward -= bump_after * 0.001

        terminated = self.engine.state.game_over
        truncated = False

        if terminated:
            reward -= 10.0
            
        return self._obs(), reward, terminated, truncated, {}

