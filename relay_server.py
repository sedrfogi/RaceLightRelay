import asyncio
import websockets
import json
import random

PORT = 8765

# State of the race light
state = {
    "phase": "waiting",  # waiting, yellow, green
    "countdown": 10
}

# Keep track of connected clients
clients = set()

async def broadcast_state():
    if clients:  # Only send if there are clients
        message = json.dumps(state)
        await asyncio.wait([client.send(message) for client in clients])

async def countdown_loop():
    while True:
        if state["phase"] == "waiting":
            state["countdown"] = 10
            await broadcast_state()
            await asyncio.sleep(1)
            state["countdown"] -= 1
            if state["countdown"] <= 0:
                state["phase"] = "yellow"
        elif state["phase"] == "yellow":
            await broadcast_state()
            delay = random.randint(1, 10)
            await asyncio.sleep(delay)
            state["phase"] = "green"
        elif state["phase"] == "green":
            await broadcast_state()
            await asyncio.sleep(3)
            state["phase"] = "waiting"

async def handle_client(websocket, path):
    clients.add(websocket)
    try:
        # Send current state immediately
        await websocket.send(json.dumps(state))
        async for _ in websocket:  # Keep connection open
            pass
    except:
        pass
    finally:
        clients.remove(websocket)

async def main():
    server = await websockets.serve(handle_client, "0.0.0.0", PORT)
    asyncio.create_task(countdown_loop())
    await server.wait_closed()

asyncio.run(main())
