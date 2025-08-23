import asyncio
import websockets
import json
from random import randint

# Keep track of all connected clients
connected_clients = set()

# Current countdown state
current_state = {
    "status": "waiting",  # can be "waiting", "be_ready", "green"
    "countdown": 10
}

async def broadcast(message):
    if connected_clients:
        await asyncio.wait([client.send(message) for client in connected_clients])

async def race_light_cycle():
    while True:
        # Wait until at least 2 clients are connected
        while len(connected_clients) < 2:
            current_state["status"] = "waiting"
            current_state["countdown"] = 10
            await asyncio.sleep(1)

        # Countdown phase
        current_state["status"] = "countdown"
        for i in range(10, 0, -1):
            current_state["countdown"] = i
            await broadcast(json.dumps(current_state))
            await asyncio.sleep(1)

        # Be Ready
        current_state["status"] = "be_ready"
        current_state["countdown"] = 0
        await broadcast(json.dumps(current_state))
        await asyncio.sleep(randint(1, 10))  # random delay

        # Green light
        current_state["status"] = "green"
        await broadcast(json.dumps(current_state))
        await asyncio.sleep(3)  # green light duration

async def handler(websocket):
    # Add new client
    connected_clients.add(websocket)

    # Send current state immediately so late joiners sync
    await websocket.send(json.dumps(current_state))

    try:
        async for message in websocket:
            pass  # We don't expect messages from clients
    finally:
        # Remove client on disconnect
        connected_clients.remove(websocket)

async def main():
    server = await websockets.serve(handler, "0.0.0.0", 8080)
    await race_light_cycle()  # run race light cycle forever

if __name__ == "__main__":
    asyncio.run(main())
