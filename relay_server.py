import asyncio
import websockets
import json
from collections import defaultdict
import random

ROOMS = defaultdict(set)  # room_name -> set of websockets

async def broadcast(room, message):
    """Send a message to all clients in the room."""
    if room in ROOMS:
        websockets_to_remove = set()
        for ws in ROOMS[room]:
            try:
                await ws.send(json.dumps(message))
            except:
                websockets_to_remove.add(ws)
        ROOMS[room] -= websockets_to_remove

async def run_race(room):
    """Run the race light sequence for a room."""
    countdown = 10
    while True:
        for i in range(countdown, 0, -1):
            await broadcast(room, {"type": "countdown", "value": i})
            await asyncio.sleep(1)
        await broadcast(room, {"type": "light", "color": "yellow"})
        delay = random.randint(1, 10)
        await asyncio.sleep(delay)
        await broadcast(room, {"type": "light", "color": "green"})
        await asyncio.sleep(3)

async def handler(ws):
    room_name = None
    task = None
    try:
        async for msg in ws:
            data = json.loads(msg)
            action = data.get("action")
            if action in ("create", "join"):
                room_name = data["room"]
                ROOMS[room_name].add(ws)
                # Start race if first player
                if len(ROOMS[room_name]) == 1:
                    task = asyncio.create_task(run_race(room_name))
            # Handle other actions if needed
    except websockets.ConnectionClosed:
        pass
    finally:
        if room_name:
            ROOMS[room_name].discard(ws)
            # Cancel race if no players left
            if not ROOMS[room_name] and task:
                task.cancel()

async def main():
    async with websockets.serve(handler, "0.0.0.0", 8080, path="/ws"):
        await asyncio.Future()  # run forever

if __name__ == "__main__":
    asyncio.run(main())
