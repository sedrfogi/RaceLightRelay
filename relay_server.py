import asyncio
import websockets
import json
from collections import defaultdict
import random

# Keep track of rooms and connected clients
rooms = defaultdict(set)  # {room_code: set(websocket, ...)}

async def broadcast(room_code, message):
    """Send message to all clients in the room."""
    if room_code in rooms:
        websockets_in_room = rooms[room_code].copy()
        for ws in websockets_in_room:
            try:
                await ws.send(message)
            except:
                rooms[room_code].discard(ws)

async def handle_client(websocket, path):
    room_code = None
    try:
        async for message in websocket:
            data = json.loads(message)

            if data["action"] == "join":
                room_code = data["room"]
                rooms[room_code].add(websocket)

                await broadcast(room_code, json.dumps({
                    "type": "info",
                    "text": f"A player joined room {room_code}. Players: {len(rooms[room_code])}"
                }))

                # Start green light loop if this is first player
                if not any(task for task in asyncio.all_tasks() if task.get_name() == f"room_{room_code}"):
                    asyncio.create_task(schedule_green_light(room_code), name=f"room_{room_code}")

    except websockets.exceptions.ConnectionClosed:
        pass
    finally:
        if room_code:
            rooms[room_code].discard(websocket)
            await broadcast(room_code, json.dumps({
                "type": "info",
                "text": f"A player left room {room_code}. Players: {len(rooms[room_code])}"
            }))

async def schedule_green_light(room_code):
    """Continuously send countdown and green light for a room."""
    while rooms[room_code]:
        # Countdown phase
        countdown = 10
        while countdown > 0:
            await broadcast(room_code, json.dumps({"type": "countdown", "seconds": countdown}))
            await asyncio.sleep(1)
            countdown -= 1

        # Be ready phase
        await broadcast(room_code, json.dumps({"type": "be_ready"}))

        # Random delay 1-10 seconds
        delay = random.randint(1, 10)
        await asyncio.sleep(delay)

        # Show green light for 3 seconds
        await broadcast(room_code, json.dumps({"type": "green"}))
        await asyncio.sleep(3)

async def main():
    async with websockets.serve(handle_client, "0.0.0.0", 8765):
        print("Relay server running on port 8765")
        await asyncio.Future()  # run forever

if __name__ == "__main__":
    asyncio.run(main())
