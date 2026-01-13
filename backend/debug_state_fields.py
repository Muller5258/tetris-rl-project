from tetris.engine import TetrisEngine

e = TetrisEngine()
print("GameState fields:", [k for k in vars(e.state).keys() if not k.startswith("_")])
