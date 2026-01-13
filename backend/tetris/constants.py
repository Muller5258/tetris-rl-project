# backend/tetris/constants.py

ROWS = 20
COLS = 10

# Timing (we can tweak later)
GRAVITY_FPS = 60               # how often we "tick" the game loop
GRAVITY_DROP_FRAMES = 30       # every N frames, the piece falls 1 cell (0.5 sec at 60fps)
SOFT_DROP_FRAMES = 2           # when soft dropping, fall faster (every 2 frames)

LOCK_DELAY_FRAMES = 30         # after touching ground, allow time to move/rotate before locking

# Scoring (classic-ish)
SCORE_SINGLE = 100
SCORE_DOUBLE = 300
SCORE_TRIPLE = 500
SCORE_TETRIS = 800
SOFT_DROP_SCORE_PER_CELL = 1   # optional: +1 per cell soft dropped
HARD_DROP_SCORE_PER_CELL = 2   # optional: +2 per cell hard dropped
