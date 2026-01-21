import argparse
from stable_baselines3.common.vec_env import SubprocVecEnv
from sb3_contrib import MaskablePPO
from tetris_rl_env import TetrisRLEnv
from stable_baselines3.common.callbacks import CheckpointCallback

def make_env(frames_per_step: int):
    return TetrisRLEnv(frames_per_step=frames_per_step)

def make_env_fn(frames_per_step):
    def _init():
        return TetrisRLEnv(frames_per_step=frames_per_step)
    return _init

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--timesteps", type=int, default=1_000_000)
    parser.add_argument("--frames-per-step", type=int, default=1)
    parser.add_argument("--n-envs", type=int, default=8)
    parser.add_argument("--model-out", type=str, default="backend/models/ppo_tetris.zip")
    args = parser.parse_args()

    env = SubprocVecEnv([make_env_fn(args.frames_per_step) for _ in range(args.n_envs)])

    model = MaskablePPO(
        "MlpPolicy",
        env,
        verbose=1,
        device="cuda",
        learning_rate=3e-4,
        n_steps=2048,
        batch_size=256,
        n_epochs=10,
        gamma=0.997,
        gae_lambda=0.95,
        clip_range=0.2,
        ent_coef=0.015,          # helps exploration early
    )
    checkpoint = CheckpointCallback(
    save_freq=200_000,                 # every 200k steps
    save_path="backend/models/checkpoints",
    name_prefix="ppo_masked",
    save_replay_buffer=False,
    save_vecnormalize=False,
)

    model.learn(total_timesteps=args.timesteps, callback=checkpoint)
    model.save(args.model_out)
    print("Saved model to:", args.model_out)


if __name__ == "__main__":
    main()
