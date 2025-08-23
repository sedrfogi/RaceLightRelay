import asyncio
import websockets
import random
import string

rooms = {}  # room_code: set of websocket connections

def generate_code():
    return ''.join(random.choices(string.digits, k=4))

async def handler(websocket):
    room_code = None
    try:
        async for message in websocket:
            if message == "CREATE":
                room_code = generate_code()
                rooms[room_code] = set()
                rooms[room_code].add(websocket)
                await websocket.send(f"ROOM_CREATED:{room_code}")
            elif message.startswith("JOIN:"):
                code = message.split(":")[1]
                if code in rooms:
                    room_code = code
                    rooms[room_code].add(websocket)
                    await websocket.send(f"JOINED:{room_code}")
                else:
                    await websocket.send("ERROR:Room not found")
            elif message == "START_CHECK":
                if room_code and len(rooms[room_code]) >= 2:
                    for ws in rooms[room_code]:
                        await ws.send("START_COUNTDOWN")
    finally:
        if room_code and websocket in rooms.get(room_code, set()):
            rooms[room_code].remove(websocket)
            if not rooms[room_code]:
                del rooms[room_code]

async def main():
    async with websockets.serve(handler, "0.0.0.0", 8765):
        print("Relay server running on port 8765")
        await asyncio.Future()

asyncio.run(main())
