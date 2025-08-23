import asyncio
import websockets
import json
import random
from collections import defaultdict

rooms = defaultdict(set)  # room_name -> set of websockets
user_rooms = {}  # websocket -> room_name

async def notify_room(room_name, message):
    if room_name in rooms:
        for ws in rooms[room_name]:
            try:
                await ws.send(json.dumps(message))
            except:
                pass

async def light_cycle(room_name):
    while rooms[room_name]:
        countdown = 10
        # Countdown
        for i in range(countdown, 0, -1):
            await notify_room(room_name, {"type": "countdown", "value": i})
            await asyncio.sleep(1)
        # Be Ready
        await notify_room(room_name, {"type": "be_ready"})
        delay = random.randint(1, 10)
        await asyncio.sleep(delay)
        # Green light
        await notify_room(room_name, {"type": "green"})
        await asyncio.sleep(3)

async def handler(websocket, path):
    room_task = None
    try:
        async for msg in websocket:
            data = json.loads(msg)
            action = data.get("action")

            if action == "create_room":
                room_name = f"room{len(rooms)+1}"
                rooms[room_name].add(websocket)
                user_rooms[websocket] = room_name
                await websocket.send(json.dumps({"type": "room_joined", "room": room_name}))
                # Start light cycle for the room
                if room_name not in asyncio.all_tasks():
                    room_task = asyncio.create_task(light_cycle(room_name))

            elif action == "join_room":
                if rooms:
                    room_name = next(iter(rooms))
                    rooms[room_name].add(websocket)
                    user_rooms[websocket] = room_name
                    await websocket.send(json.dumps({"type": "room_joined", "room": room_name}))

    except websockets.ConnectionClosed:
        pass
    finally:
        # Remove from room
        room_name = user_rooms.get(websocket)
        if room_name and websocket in rooms[room_name]:
            rooms[room_name].remove(websocket)
            if not rooms[room_name]:
                del rooms[room_name]
        if websocket in user_rooms:
            del user_rooms[websocket]
        if room_task:
            room_task.cancel()

async def main():
    async with websockets.serve(handler, "0.0.0.0", 8080):
        print("Relay server running on ws://0.0.0.0:8080")
        await asyncio.Future()  # run forever

if __name__ == "__main__":
    asyncio.run(main())
