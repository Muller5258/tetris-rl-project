import asyncio
from html import parser
import json
import websockets
import argparse
import time
import os

from stable_baselines3 import PPO
from tetris_rl_env import TetrisRLEnv
from tetris.constants import GRAVITY_FPS
from csv_logger import CSVLogger
from datetime import datetime
from sb3_contrib import MaskablePPO

MODEL_MAP = {
    "latest": "models/ppo_masked_v6",  # or wherever latest points
    "phase2": "models/ppo_tetris_phase2",
    "phase25": "models/ppo_tetris_phase25",
    "masked_v6": "models/ppo_masked_v6",
    "masked_v5": "models/ppo_masked_v5",
}

CLIENTS = set()
CURRENT_FPS = GRAVITY_FPS

def load_any_model(path: str):
    try:
        return MaskablePPO.load(path)
    except Exception:
        return PPO.load(path)

async def handler(websocket):
    CLIENTS.add(websocket)
    print("Client connected!")
    try:
        async for message in websocket:
            try:
                data = json.loads(message)
            except:
                continue

            # config message from frontend
            if data.get("type") == "config":
                await broadcast({"type": "config_ack", "ok": True, "received": data})
                websocket.config_message = data  # stash on socket object
    finally:
        CLIENTS.discard(websocket)
        print("Client disconnected!")

async def broadcast(payload: dict):
    if not CLIENTS:
        return
    msg = json.dumps(payload)
    dead = []
    for ws in list(CLIENTS):
        try:
            await ws.send(msg)
        except:
            dead.append(ws)
    for ws in dead:
        CLIENTS.discard(ws)

async def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", type=str, default="models/ppo_tetris_phase2")
    parser.add_argument("--log-steps", type=str, default="logs/steps.csv")
    parser.add_argument("--log-episodes", type=str, default="logs/episodes.csv")
    parser.add_argument("--flush-every", type=int, default=200)
    parser.add_argument("--host", type=str, default="0.0.0.0")
    parser.add_argument("--port", type=int, default=8765)
    args = parser.parse_args()
    run_id = datetime.now().strftime("%Y%m%d_%H%M%S")
    run_dir = os.path.join("logs", "runs", run_id)
    os.makedirs(run_dir, exist_ok=True)

    args.log_steps = os.path.join(run_dir, "steps.csv")
    args.log_episodes = os.path.join(run_dir, "episodes.csv")

    print("Logging to:", run_dir)


    steps_logger = CSVLogger(
        path=args.log_steps,
        fieldnames=["run_id", "wall_time", "episode", "step", "reward", "score", "lines", "game_over"],
        flush_every=args.flush_every,
    )
    episodes_logger = CSVLogger(
        path=args.log_episodes,
        fieldnames=["run_id", "wall_time", "episode", "steps", "total_reward", "lines", "score"],
        flush_every=1,  # flush each episode end
    )
    steps_logger.open()
    episodes_logger.open()

    print("Loading model...")
    model = load_any_model(args.model)
    env = TetrisRLEnv(frames_per_step=6)
    current_fps = GRAVITY_FPS
    current_model_name = "phase2"


    print("WebSocket server running on ws://localhost:8765")
    async with websockets.serve(handler, args.host, args.port):
        print(f"WebSocket server running on ws://{args.host}:{args.port}")
        try:
            obs, _ = env.reset()
            episode = 0
            ep_reward = 0.0
            ep_steps = 0
            step = 0
            while True:
                # apply latest config from any client (last one wins)
                for ws in list(CLIENTS):
                    cfg = getattr(ws, "config_message", None)
                    if cfg:
                        # model swap
                        if "model" in cfg:
                            name = cfg["model"]
                            if name in MODEL_MAP and name != current_model_name:
                                print("Switching model to:", name)
                                model = load_any_model(MODEL_MAP[name])
                                current_model_name = name

                        # fps change
                        if "fps" in cfg:
                            try:
                                f = float(cfg["fps"])
                                if f > 0:
                                    current_fps = f
                            except:
                                pass

                        # clear so we don't reapply every frame
                        ws.config_message = None

                # model chooses action
                action, _ = model.predict(obs, deterministic=True)
                obs, reward, done, truncated, _ = env.step(int(action))

                ep_reward += float(reward)
                ep_steps += 1
                step += 1

                # per-step log
                steps_logger.log({
                    "run_id": run_id,
                    "wall_time": time.time(),
                    "episode": episode,
                    "step": ep_steps,
                    "reward": float(reward),
                    "score": int(env.engine.state.score),
                    "lines": int(env.engine.state.lines),
                    "game_over": bool(env.engine.state.game_over),
                })

                # send state to UI
                await broadcast({
                    "type": "state",
                    "board": env.engine.to_render_board(),
                    "score": env.engine.state.score,
                    "lines": env.engine.state.lines,
                    "nextPiece": env.engine.state.next_piece_id,
                    "gameOver": env.engine.state.game_over,
                    "aiAction": int(action),
                    "reward": float(reward),
                    "episode": episode,
                    "step": step,
                })

                # end of episode
                if done or truncated:
                    episodes_logger.log({
                        "run_id": run_id,
                        "wall_time": time.time(),
                        "episode": episode,
                        "steps": ep_steps,
                        "total_reward": float(ep_reward),
                        "lines": int(env.engine.state.lines),
                        "score": int(env.engine.state.score),
                    })
                    episodes_logger.flush()

                    episode += 1
                    step = 0
                    ep_reward = 0.0
                    ep_steps = 0

                    await asyncio.sleep(0.8)
                    obs, _ = env.reset()

                # real-time speed (roughly)
                await asyncio.sleep(1.0 / current_fps)

        finally:
            steps_logger.close()
            episodes_logger.close()

if __name__ == "__main__":
    asyncio.run(main())
