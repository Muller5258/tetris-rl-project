from tetris_rl_env import TetrisRLEnv

env = TetrisRLEnv(frames_per_step=6)

obs, _ = env.reset()
total_reward = 0.0
steps = 0

while True:
    action = env.action_space.sample()
    obs, reward, done, truncated, info = env.step(action)
    total_reward += reward
    steps += 1
    if done or truncated or steps >= 2000:
        break

print("Random run finished:")
print("steps:", steps)
print("total_reward:", total_reward)
print("lines:", env.engine.state.lines)
print("score:", env.engine.state.score)
