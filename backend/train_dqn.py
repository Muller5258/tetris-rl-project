import argparse
from stable_baselines3 import DQN
from stable_baselines3.common.vec_env import SubprocVecEnv

from tetris_rl_env import TetrisRLEnv


def make_env(frames_per_step: int):
    # Important: return a NEW env each time
    return TetrisRLEnv(frames_per_step=frames_per_step)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--timesteps", type=int, default=300_000)
    parser.add_argument("--frames-per-step", type=int, default=1)
    parser.add_argument("--model-out", type=str, default="backend/models/dqn_tetris.zip")
    parser.add_argument("--n-envs", type=int, default=8)
    args = parser.parse_args()

    env = SubprocVecEnv([lambda: make_env(args.frames_per_step) for _ in range(args.n_envs)])

    model = DQN(
        "MlpPolicy",
        env,
        verbose=1,
        device="cuda",
        learning_rate=1e-4,
        buffer_size=200_000,
        learning_starts=10_000,
        batch_size=256,
        gamma=0.99,
        train_freq=4,
        target_update_interval=5_000,
        exploration_fraction=0.2,
        exploration_final_eps=0.05,
    )

    model.learn(total_timesteps=args.timesteps)
    model.save(args.model_out)
    print("Saved model to:", args.model_out)


if __name__ == "__main__":
    main()

