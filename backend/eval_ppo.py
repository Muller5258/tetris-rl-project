import argparse
from stable_baselines3 import PPO

from tetris_rl_env import TetrisRLEnv


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", type=str, default="backend/models/ppo_tetris.zip")
    parser.add_argument("--deterministic", action="store_true")
    args = parser.parse_args()

    env = TetrisRLEnv(frames_per_step=1)
    model = PPO.load(args.model)

    obs, _ = env.reset()
    total_reward = 0.0
    steps = 0

    while True:
        action, _ = model.predict(obs, deterministic=args.deterministic)
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


if __name__ == "__main__":
    main()

