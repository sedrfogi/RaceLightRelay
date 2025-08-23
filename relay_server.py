import asyncio
import websockets

# Keep track of all connected clients
connected_clients = set()

async def relay_handler(websocket):
    # Add new client
    connected_clients.add(websocket)
    try:
        async for message in websocket:
            # Broadcast message to all other clients
            for client in connected_clients:
                if client != websocket:
                    await client.send(message)
    except websockets.ConnectionClosed:
        pass
    finally:
        connected_clients.remove(websocket)

# Start the WebSocket server
async def main():
    async with websockets.serve(relay_handler, "0.0.0.0", 8765):
        print("Relay server running on port 8765")
        await asyncio.Future()  # Keep running forever

# Only define the main coroutine, DO NOT call asyncio.run()
# Railway will start this file as a background worker
