import asyncio
import json
import websockets

from tetris.engine import TetrisEngine
from tetris.constants import GRAVITY_FPS

CLIENTS = set()
ENGINE = TetrisEngine()


async def handler(websocket):
    CLIENTS.add(websocket)
    print("Client connected!")

    try:
        async for message in websocket:
            data = json.loads(message)

            if data["type"] == "input":
                action = data["action"]

                if action == "left":
                    ENGINE.move_left()
                elif action == "right":
                    ENGINE.move_right()
                elif action == "rotate":
                    ENGINE.rotate_cw()
                elif action == "soft_drop_on":
                    ENGINE.set_soft_drop(True)
                elif action == "soft_drop_off":
                    ENGINE.set_soft_drop(False)
                elif action == "hard_drop":
                    ENGINE.hard_drop()

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


async def game_loop():
    global ENGINE
    while True:
        ENGINE.tick()

        await broadcast({
            "type": "state",
            "board": ENGINE.to_render_board(),
            "score": ENGINE.state.score,
            "nextPiece": ENGINE.state.next_piece_id,
            "gameOver": ENGINE.state.game_over,
        })

        if ENGINE.state.game_over:
            await asyncio.sleep(1)
            ENGINE = TetrisEngine()

        await asyncio.sleep(1.0 / GRAVITY_FPS)


async def main():
    print("WebSocket server running on ws://localhost:8765")
    async with websockets.serve(handler, "localhost", 8765):
        await game_loop()


if __name__ == "__main__":
    asyncio.run(main())
