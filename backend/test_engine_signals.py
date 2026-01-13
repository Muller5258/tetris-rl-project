from tetris.engine import TetrisEngine

engine = TetrisEngine()

print("Starting...")
print("Gravity frames:", engine.state.frame)

for i in range(1200):  # ~20 seconds
    engine.tick()

    # Print every second to prove time advances
    if i % 60 == 0:
        print("i=", i, "frame=", engine.state.frame, "piece_row=", engine.state.active.row, "lock_timer=", engine.state.lock_timer)

    # This should print once per lock if signals work
    if hasattr(engine.state, "just_locked") and engine.state.just_locked:
        print("LOCK! cleared =", engine.state.just_cleared, "score =", engine.state.score)

print("done")
