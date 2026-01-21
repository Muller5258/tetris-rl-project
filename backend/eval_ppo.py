import argparse
import numpy as np
from sb3_contrib import MaskablePPO
from tetris_rl_env import TetrisRLEnv
from stable_baselines3 import PPO

def run_one(model: PPO, deterministic: bool) -> tuple[int, float, int, int]:
    env = TetrisRLEnv(frames_per_step=1)
    obs, _ = env.reset()

    total_reward = 0.0
    steps = 0

    while True:
        action, _ = model.predict(obs, deterministic=deterministic)
        obs, reward, done, truncated, _ = env.step(int(action))
        total_reward += float(reward)
        steps += 1

        if done or truncated or steps >= 5000:
            break

    lines = env.engine.state.lines
    score = env.engine.state.score
    return steps, total_reward, lines, score


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", type=str, default="backend/models/ppo_tetris.zip")
    parser.add_argument("--deterministic", action="store_true")
    parser.add_argument("--episodes", type=int, default=10)
    args = parser.parse_args()

    try:
        model = MaskablePPO.load(args.model)
        print("Loaded as MaskablePPO")
    except Exception:
        model = PPO.load(args.model)
        print("Loaded as PPO")

    steps_list = []
    reward_list = []
    lines_list = []
    score_list = []

    for _ in range(args.episodes):
        steps, total_reward, lines, score = run_one(model, args.deterministic)
        steps_list.append(steps)
        reward_list.append(total_reward)
        lines_list.append(lines)
        score_list.append(score)

    print(f"Eval over {args.episodes} episode(s):")
    print(
        "avg steps:", round(float(np.mean(steps_list)), 2),
        "min/max:", min(steps_list), max(steps_list)
    )
    print("avg reward:", round(float(np.mean(reward_list)), 4))
    print(
        "avg lines:", round(float(np.mean(lines_list)), 2),
        "min/max:", min(lines_list), max(lines_list)
    )
    print(
        "avg score:", round(float(np.mean(score_list)), 2),
        "min/max:", min(score_list), max(score_list)
    )


if __name__ == "__main__":
    main()
