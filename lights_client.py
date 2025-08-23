import tkinter as tk
import asyncio
import threading
import json
import random
import websockets

# Read server URL from config.txt
with open("config.txt", "r") as f:
    SERVER_URL = f.read().strip()

class RaceLightApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Race Light")
        self.root.configure(bg="#222222")
        self.root.attributes("-topmost", True)
        self.root.geometry("250x300")

        self.room_name = tk.StringVar()

        # Room entry
        tk.Label(root, text="Room Name:", fg="white", bg="#222222").pack(pady=5)
        self.room_entry = tk.Entry(root, textvariable=self.room_name)
        self.room_entry.pack()

        # Buttons
        self.create_btn = tk.Button(root, text="Create Room", command=self.create_room)
        self.create_btn.pack(pady=5)
        self.join_btn = tk.Button(root, text="Join Room", command=self.join_room)
        self.join_btn.pack(pady=5)

        # Countdown label & circle
        self.text_label = tk.Label(root, text="", font=("Arial", 18), fg="white", bg="#222222")
        self.text_label.pack(pady=10)

        self.canvas = tk.Canvas(root, width=100, height=100, bg="#222222", highlightthickness=0)
        self.canvas.pack(pady=10)
        self.circle = self.canvas.create_oval(10, 10, 90, 90, fill="grey")

        # WebSocket
        self.ws = None
        self.loop = asyncio.new_event_loop()
        threading.Thread(target=self.loop.run_forever, daemon=True).start()

    # WebSocket helpers
    async def connect_ws(self):
        async with websockets.connect(SERVER_URL) as websocket:
            self.ws = websocket
            await self.listen_ws()

    async def listen_ws(self):
        async for message in self.ws:
            data = json.loads(message)
            if data["type"] == "countdown":
                self.update_countdown(data["value"])
            elif data["type"] == "light":
                self.update_light(data["color"])

    def start_ws_thread(self):
        asyncio.run_coroutine_threadsafe(self.connect_ws(), self.loop)

    # Room actions
    def create_room(self):
        room = self.room_name.get()
        if room:
            asyncio.run_coroutine_threadsafe(self.send_ws({"action": "create", "room": room}), self.loop)
            self.start_ws_thread()

    def join_room(self):
        room = self.room_name.get()
        if room:
            asyncio.run_coroutine_threadsafe(self.send_ws({"action": "join", "room": room}), self.loop)
            self.start_ws_thread()

    async def send_ws(self, message):
        if self.ws:
            await self.ws.send(json.dumps(message))

    # Update GUI
    def update_countdown(self, value):
        self.text_label.config(text=f"Next light {value}")

    def update_light(self, color):
        self.canvas.itemconfig(self.circle, fill=color)

def main():
    root = tk.Tk()
    app = RaceLightApp(root)
    root.mainloop()

if __name__ == "__main__":
    main()
