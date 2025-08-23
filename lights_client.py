import asyncio
import tkinter as tk
from tkinter import simpledialog
import websockets
import threading

RELAY_URL = "wss://racelightrelay-production.up.railway.app/ws"

class RaceLightApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Race Light Sync")
        self.root.geometry("300x150")
        self.root.attributes("-topmost", True)  # Always on top
        self.root.configure(bg="black")

        # Initialize websocket as None
        self.websocket = None  

        self.status_label = tk.Label(root, text="Not connected", fg="white", bg="black")
        self.status_label.pack(pady=10)

        self.create_btn = tk.Button(root, text="Create Room", command=self.create_room)
        self.create_btn.pack(pady=5)

        self.join_btn = tk.Button(root, text="Join Room", command=self.join_room)
        self.join_btn.pack(pady=5)

        # Run websocket connection in background
        threading.Thread(target=self.start_ws, daemon=True).start()

    async def ws_handler(self):
        async with websockets.connect(RELAY_URL) as ws:
            self.websocket = ws
            self.status_label.config(text="Connected to relay")

            async for msg in ws:
                print("Received:", msg)

    def start_ws(self):
        asyncio.run(self.ws_handler())

    def create_room(self):
        if self.websocket:
            asyncio.run_coroutine_threadsafe(
                self.websocket.send('{"action": "create"}'),
                asyncio.get_running_loop()
            )
            self.status_label.config(text="Room created!")
            self.create_btn.pack_forget()
            self.join_btn.pack_forget()
        else:
            self.status_label.config(text="Not connected yet")

    def join_room(self):
        if self.websocket:
            room_code = simpledialog.askstring("Join Room", "Enter room code:")
            if room_code:
                asyncio.run_coroutine_threadsafe(
                    self.websocket.send(f'{{"action": "join", "room": "{room_code}"}}'),
                    asyncio.get_running_loop()
                )
                self.status_label.config(text=f"Joined room {room_code}!")
                self.create_btn.pack_forget()
                self.join_btn.pack_forget()
        else:
            self.status_label.config(text="Not connected yet")

if __name__ == "__main__":
    root = tk.Tk()
    app = RaceLightApp(root)
    root.mainloop()
