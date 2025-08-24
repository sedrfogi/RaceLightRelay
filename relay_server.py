import asyncio
import websockets
import json
import random
import time

# Rooms = { room_code: { "clients": set(), "state": {...} } }
rooms = {}

async def broadcast(room_code, message):
    """Send message to all clients in a room."""
    if room_code in rooms:
        to_remove = set()
        for client in rooms[room_code]["clients"]:
            try:
                await client.send(json.dumps(message))
            except:
                to_remove.add(client)
        rooms[room_code]["clients"] -= to_remove
        if not rooms[room_code]["clients"]:
            del rooms[room_code]

async def light_loop(room_code):
    """Continuously loop the race light sequence for a room."""
    while room_code in rooms:
        # Countdown 10 → 1
        for sec in range(10, 0, -1):
            rooms[room_code]["state"] = {"type": "state", "event": "countdown", "time": sec}
            await broadcast(room_code, rooms[room_code]["state"])
            await asyncio.sleep(1)

        # Be ready
        rooms[room_code]["state"] = {"type": "state", "event": "ready"}
        await broadcast(room_code, rooms[room_code]["state"])

        # Random delay for green light
        delay = random.randint(1, 10)
        rooms[room_code]["state"] = {"type": "state", "event": "green_time", "delay": delay, "start": time.time()}
        await asyncio.sleep(delay)

        # Green light
        rooms[room_code]["state"] = {"type": "state", "event": "green"}
        await broadcast(room_code, rooms[room_code]["state"])

        await asyncio.sleep(3)  # Green light stays 3s

async def handler(websocket):
    room_code = None
    try:
        async for message in websocket:
            try:
                data = json.loads(message.replace("'", '"'))
            except json.JSONDecodeError:
                await websocket.send(json.dumps({"error": "Invalid message format"}))
                continue

            action = data.get("action")
            room = data.get("room")

            if action == "create":
                room_code = room
                if room_code not in rooms:
                    rooms[room_code] = {"clients": set(), "state": None}
                rooms[room_code]["clients"].add(websocket)
                await websocket.send(json.dumps({"message": f"Room {room_code} created!"}))
                print(f"Client created room {room_code}")

                # Start looping lights for this room
                asyncio.create_task(light_loop(room_code))

            elif action == "join":
                room_code = room
                if room_code in rooms:
                    rooms[room_code]["clients"].add(websocket)
                    await websocket.send(json.dumps({"message": f"Joined room {room_code}"}))
                    print(f"Client joined room {room_code}")
                    # Send current state immediately to sync
                    if rooms[room_code]["state"]:
                        await websocket.send(json.dumps(rooms[room_code]["state"]))
                else:
                    await websocket.send(json.dumps({"error": f"Room {room_code} does not exist."}))

            else:
                # Broadcast other messages
                if room_code and room_code in rooms:
                    await broadcast(room_code, data)

    except Exception as e:
        print("Client error:", e)
    finally:
        if room_code and room_code in rooms and websocket in rooms[room_code]["clients"]:
            rooms[room_code]["clients"].remove(websocket)
            if not rooms[room_code]["clients"]:
                del rooms[room_code]
            print(f"Client left room {room_code}")

async def main():
    async with websockets.serve(handler, "0.0.0.0", 8080):
        print("Relay server running on ws://0.0.0.0:8080")
        await asyncio.Future()  # run forever

if __name__ == "__main__":
    asyncio.run(main())
