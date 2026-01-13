from tetris_rl_env import TetrisRLEnv

env = TetrisRLEnv(frames_per_step=1)
obs, _ = env.reset()

placements = env._valid_actions()
print("valid placements:", len(placements), placements[:10])

for i in range(min(10, len(placements))):
    obs, r, done, trunc, _ = env.step(i)
    if done:
        print("died on action", i)
        break

print("score:", env.engine.state.score, "lines:", env.engine.state.lines)
