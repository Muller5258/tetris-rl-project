import asyncio
import json
import websockets

from stable_baselines3 import PPO

from tetris_rl_env import TetrisRLEnv
from tetris.constants import GRAVITY_FPS


CLIENTS = set()


async def handler(websocket):
    CLIENTS.add(websocket)
    print("Client connected!")
    try:
        await websocket.wait_closed()
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
    print("Loading model...")
    model = PPO.load("models/ppo_tetris_phase2")
    env = TetrisRLEnv(frames_per_step=6)

    print("WebSocket server running on ws://localhost:8765")
    async with websockets.serve(handler, "localhost", 8765):

        obs, _ = env.reset()
        episode = 0
        step = 0
        while True:
            # model chooses action
            action, _ = model.predict(obs, deterministic=True)
            obs, reward, done, truncated, _ = env.step(int(action))
            step += 1

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

            if done or truncated:
                episode += 1
                step = 0
                await asyncio.sleep(0.8)
                obs, _ = env.reset()

            # real-time speed (roughly)
            await asyncio.sleep(1.0 / GRAVITY_FPS)


if __name__ == "__main__":
    asyncio.run(main())
