import argparse
from stable_baselines3 import PPO
from stable_baselines3.common.vec_env import SubprocVecEnv

from tetris_rl_env import TetrisRLEnv


def make_env(frames_per_step: int):
    return TetrisRLEnv(frames_per_step=frames_per_step)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--timesteps", type=int, default=1_000_000)
    parser.add_argument("--frames-per-step", type=int, default=1)
    parser.add_argument("--n-envs", type=int, default=8)
    parser.add_argument("--model-out", type=str, default="backend/models/ppo_tetris.zip")
    args = parser.parse_args()

    env = SubprocVecEnv([lambda: make_env(args.frames_per_step) for _ in range(args.n_envs)])

    model = PPO(
         "MlpPolicy",
          env,
          verbose=1,
          device="cuda",
          n_steps=1024,
          batch_size=256,
          gamma=0.99,
          gae_lambda=0.95,
          n_epochs=10,
          learning_rate=3e-4,
          ent_coef=0.10,     # MORE exploration
          clip_range=0.2,
          )


    model.learn(total_timesteps=args.timesteps)
    model.save(args.model_out)
    print("Saved model to:", args.model_out)


if __name__ == "__main__":
    main()
