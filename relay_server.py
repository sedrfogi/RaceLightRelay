# relay_server.py
import os
import json
import asyncio
import random
import websockets
from websockets.server import WebSocketServerProtocol

"""
Protocol (JSON only):
Client -> Server:
  {"action": "create", "room": "1234"}
  {"action": "join",   "room": "1234"}

Server -> Client (broadcasts and info):
  {"type":"info","message":"..."}
  {"type":"state","event":"countdown","time":10}   # time = 10..1
  {"type":"state","event":"ready"}                 # yellow appears
  {"type":"state","event":"green"}                 # green appears (for 3s)

Design:
- Each room has:
    {
      "clients": set[WebSocketServerProtocol],
      "task": asyncio.Task,
      "last_state": dict | None
    }
- light_cycle updates last_state before broadcasting, so new joiners can be
  immediately given the current state (best-effort sync).
"""

Room = dict
rooms: dict[str, Room] = {}


async def broadcast(room_code: str, payload: dict):
    """Send payload to all clients in a room. Remove dead sockets."""
    if room_code not in rooms:
        return
    dead = []
    msg = json.dumps(payload)
    for ws in list(rooms[room_code]["clients"]):
        try:
            await ws.send(msg)
        except Exception:
            dead.append(ws)
    for ws in dead:
        rooms[room_code]["clients"].discard(ws)


async def light_cycle(room_code: str):
    """Run forever while room exists: countdown -> ready -> random wait -> green -> 3s -> repeat."""
    try:
        while room_code in rooms:
            # Countdown 10..1
            for t in range(10, 0, -1):
                state = {"type": "state", "event": "countdown", "time": t}
                rooms[room_code]["last_state"] = state
                await broadcast(room_code, state)
                await asyncio.sleep(1)

            # Be ready (yellow)
            state = {"type": "state", "event": "ready"}
            rooms[room_code]["last_state"] = state
            await broadcast(room_code, state)
            await asyncio.sleep(1)

            # Random 1..10 seconds before green
            delay = random.randint(1, 10)
            await asyncio.sleep(delay)

            # Green for 3 seconds
            state = {"type": "state", "event": "green"}
            rooms[room_code]["last_state"] = state
            await broadcast(room_code, state)
            await asyncio.sleep(3)
    except asyncio.CancelledError:
        # Normal room shutdown
        pass
    except Exception as e:
        # Log and try to keep server alive
        print(f"[room {room_code}] light_cycle error:", e)


async def ensure_room(room_code: str):
    """Create room data if missing."""
    if room_code not in rooms:
        rooms[room_code] = {"clients": set(), "task": None, "last_state": None}


async def start_cycle_if_needed(room_code: str):
    """Start the light cycle for the room if not running."""
    room = rooms.get(room_code)
    if room and (room["task"] is None or room["task"].done()):
        room["task"] = asyncio.create_task(light_cycle(room_code))


async def stop_cycle_if_empty(room_code: str):
    """Stop cycle and delete room if no clients."""
    room = rooms.get(room_code)
    if not room:
        return
    if not room["clients"]:
        task = room.get("task")
        if task and not task.done():
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass
        rooms.pop(room_code, None)
        print(f"[room {room_code}] deleted (empty)")


async def handle_client(ws: WebSocketServerProtocol):
    room_code = None
    try:
        async for raw in ws:
            try:
                data = json.loads(raw)
            except json.JSONDecodeError:
                await ws.send(json.dumps({"type": "info", "message": "Invalid JSON"}))
                continue

            action = data.get("action")
            code = data.get("room")

            if action == "create" and code:
                room_code = code
                await ensure_room(room_code)
                rooms[room_code]["clients"].add(ws)
                await ws.send(json.dumps({"type": "info", "message": f"Room {room_code} created"}))
                await start_cycle_if_needed(room_code)
                print(f"Client created/joined room {room_code} (create)")
                # Immediately send last known state (if any) for late sync
                if rooms[room_code]["last_state"]:
                    await ws.send(json.dumps(rooms[room_code]["last_state"]))

            elif action == "join" and code:
                if code not in rooms:
                    await ws.send(json.dumps({"type": "info", "message": f"Room {code} does not exist"}))
                    continue
                room_code = code
                rooms[room_code]["clients"].add(ws)
                await ws.send(json.dumps({"type": "info", "message": f"Joined room {room_code}"}))
                print(f"Client joined room {room_code}")
                # Late-join snapshot
                if rooms[room_code]["last_state"]:
                    await ws.send(json.dumps(rooms[room_code]["last_state"]))

            else:
                await ws.send(json.dumps({"type": "info", "message": "Unknown action or missing room"}))

    except websockets.ConnectionClosed:
        pass
    except Exception as e:
        print("Client handler error:", e)
    finally:
        # cleanup
        if room_code and room_code in rooms and ws in rooms[room_code]["clients"]:
            rooms[room_code]["clients"].discard(ws)
            print(f"Client left room {room_code}")
            await stop_cycle_if_empty(room_code)


async def main():
    port = int(os.getenv("PORT", "8080"))  # Railway will set PORT
    host = "0.0.0.0"
    print(f"Relay server starting on ws://{host}:{port}")
    async with websockets.serve(
        handle_client,
        host,
        port,
        ping_interval=20,
        ping_timeout=20,
        max_size=1_000_000,
    ):
        print("Relay server running")
        await asyncio.Future()

if __name__ == "__main__":
    asyncio.run(main())
