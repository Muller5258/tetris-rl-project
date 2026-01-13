from tetris_rl_env import TetrisRLEnv

env = TetrisRLEnv(frames_per_step=1)
obs, _ = env.reset()

steps = 0
while True:
    action = env.action_space.sample()
    obs, reward, done, truncated, _ = env.step(action)
    steps += 1
    if done or truncated or steps >= 200:
        break

print("Random macro eval:")
print("steps:", steps)
print("lines:", env.engine.state.lines)
print("score:", env.engine.state.score)
