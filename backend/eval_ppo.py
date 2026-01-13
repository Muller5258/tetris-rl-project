from stable_baselines3 import PPO
from tetris_rl_env import TetrisRLEnv

env = TetrisRLEnv(frames_per_step=1)
model = PPO.load("backend/models/ppo_tetris.zip")

obs, _ = env.reset()
total_reward = 0.0
steps = 0

while True:
    action, _ = model.predict(obs, deterministic=True)
    obs, reward, done, truncated, _ = env.step(int(action))
    total_reward += reward
    steps += 1
    if done or truncated or steps >= 5000:
        break

print("Eval finished:")
print("steps:", steps)
print("total_reward:", total_reward)
print("lines:", env.engine.state.lines)
print("score:", env.engine.state.score)
