import asyncio
import websockets
import json

# Rooms = { room_code: set_of_clients }
rooms = {}

async def handler(websocket):
    room_code = None
    try:
        async for message in websocket:
            print("Received raw:", message)

            try:
                data = json.loads(message.replace("'", '"'))  # handle ' vs "
            except json.JSONDecodeError:
                await websocket.send("Invalid message format")
                continue

            action = data.get("action")
            room = data.get("room")

            if action == "create":
                room_code = room
                if room_code not in rooms:
                    rooms[room_code] = set()
                rooms[room_code].add(websocket)
                await websocket.send(f"Room {room_code} created!")
                print(f"Client created room {room_code}")

            elif action == "join":
                room_code = room
                if room_code in rooms:
                    rooms[room_code].add(websocket)
                    await websocket.send(f"Joined room {room_code}")
                    print(f"Client joined room {room_code}")
                else:
                    await websocket.send(f"Room {room_code} does not exist.")

            else:
                # Broadcast message to everyone else in the same room
                if room_code and room_code in rooms:
                    for client in rooms[room_code]:
                        if client != websocket:
                            try:
                                await client.send(message)
                            except:
                                pass
    except Exception as e:
        print("Client error:", e)
    finally:
        # Cleanup when client disconnects
        if room_code and room_code in rooms and websocket in rooms[room_code]:
            rooms[room_code].remove(websocket)
            if not rooms[room_code]:
                del rooms[room_code]  # remove empty room
            print(f"Client left room {room_code}")

async def main():
    async with websockets.serve(handler, "0.0.0.0", 8080):
        print("Relay server running on ws://0.0.0.0:8080")
        await asyncio.Future()  # run forever

if __name__ == "__main__":
    asyncio.run(main())
