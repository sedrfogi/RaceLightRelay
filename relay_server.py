# relay_server.py
from fastapi import FastAPI, WebSocket
from fastapi.middleware.cors import CORSMiddleware
import asyncio

app = FastAPI()

# Allow all origins so your clients can connect
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Keep track of all connected clients
connected_clients = set()

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    connected_clients.add(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            # Broadcast the received message to all clients
            for client in connected_clients:
                if client != websocket:
                    await client.send_text(data)
    except Exception:
        pass
    finally:
        connected_clients.remove(websocket)

# Optional: run a periodic ping to keep connections alive
async def ping_clients():
    while True:
        await asyncio.sleep(30)
        for client in list(connected_clients):
            try:
                await client.send_text("ping")
            except:
                connected_clients.remove(client)

# Start the ping loop in the background
@app.on_event("startup")
async def startup_event():
    asyncio.create_task(ping_clients())
