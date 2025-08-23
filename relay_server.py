from fastapi import FastAPI, WebSocket, WebSocketDisconnect
import random
import string

app = FastAPI()
rooms = {}  # room_code: set of websockets

def generate_code():
    return ''.join(random.choices(string.digits, k=4))

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    room_code = None
    try:
        while True:
            data = await websocket.receive_text()
            if data == "CREATE":
                room_code = generate_code()
                rooms[room_code] = set()
                rooms[room_code].add(websocket)
                await websocket.send_text(f"ROOM_CREATED:{room_code}")
            elif data.startswith("JOIN:"):
                code = data.split(":")[1]
                if code in rooms:
                    room_code = code
                    rooms[room_code].add(websocket)
                    await websocket.send_text(f"JOINED:{room_code}")
                else:
                    await websocket.send_text("ERROR:Room not found")
            elif data == "START_CHECK":
                if room_code and len(rooms[room_code]) >= 2:
                    for ws in rooms[room_code]:
                        await ws.send_text("START_COUNTDOWN")
    except WebSocketDisconnect:
        if room_code and websocket in rooms.get(room_code, set()):
            rooms[room_code].remove(websocket)
            if not rooms[room_code]:
                del rooms[room_code]
