from fastapi import FastAPI, WebSocket
from fastapi.middleware.cors import CORSMiddleware
import asyncio
import random

app = FastAPI()

# Allow connections from anywhere
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

rooms = {}  # room_code -> set of websockets

@app.websocket("/ws/{room_code}")
async def websocket_endpoint(websocket: WebSocket, room_code: str):
    await websocket.accept()
    if room_code not in rooms:
        rooms[room_code] = set()
    rooms[room_code].add(websocket)

    try:
        # Start syncing only if 2 or more players are in the room
        while True:
            if len(rooms[room_code]) >= 2:
                countdown = 10
                # Send countdown
                for ws in rooms[room_code]:
                    await ws.send_json({"type": "countdown", "value": countdown})
                await asyncio.sleep(1)
                for i in range(countdown-1, 0, -1):
                    for ws in rooms[room_code]:
                        await ws.send_json({"type": "countdown", "value": i})
                    await asyncio.sleep(1)

                # Be Ready
                for ws in rooms[room_code]:
                    await ws.send_json({"type": "be_ready"})
                
                delay = random.randint(1, 10)
                await asyncio.sleep(delay)

                # Green light
                for ws in rooms[room_code]:
                    await ws.send_json({"type": "green"})
                
                await asyncio.sleep(3)  # green light duration
            else:
                await asyncio.sleep(1)
    except:
        pass
    finally:
        rooms[room_code].remove(websocket)
        if len(rooms[room_code]) == 0:
            del rooms[room_code]
