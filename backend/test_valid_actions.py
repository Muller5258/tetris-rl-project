from tetris_rl_env import TetrisRLEnv

env = TetrisRLEnv(frames_per_step=1)
obs, _ = env.reset()

valid = env._valid_actions_set()
print("valid placements:", len(valid))
print(sorted(list(valid))[:10], "...")

