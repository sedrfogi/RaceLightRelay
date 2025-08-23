import asyncio
import websockets
from http.server import BaseHTTPRequestHandler, HTTPServer
import threading

# --- CONFIG ---
WS_PORT = 8765  # WebSocket port
HTTP_PORT = 8766  # HTTP health check port

# --- WebSocket handler ---
connected_clients = set()

async def ws_handler(websocket, path):
    connected_clients.add(websocket)
    try:
        async for message in websocket:
            # echo back or handle messages here
            await websocket.send(message)
    finally:
        connected_clients.remove(websocket)

# --- HTTP health check ---
class HealthHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"OK")

def run_http_server():
    server = HTTPServer(('0.0.0.0', HTTP_PORT), HealthHandler)
    print(f"HTTP health check server running on port {HTTP_PORT}")
    server.serve_forever()

# --- START SERVERS ---
# Start HTTP health server in a separate thread
threading.Thread(target=run_http_server, daemon=True).start()

# Start WebSocket server
start_server = websockets.serve(ws_handler, "0.0.0.0", WS_PORT)
asyncio.get_event_loop().run_until_complete(start_server)
print(f"WebSocket server running on port {WS_PORT}")
asyncio.get_event_loop().run_forever()
