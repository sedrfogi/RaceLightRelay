import asyncio
import threading
import tkinter as tk
from tkinter import simpledialog, messagebox
import websockets

SERVER_URL = "ws://localhost:8080"  # change to your relay server URL

class RaceLightApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Race Light Sync")
        self.root.configure(bg="black")

        # Always on top, remove extra controls
        self.root.overrideredirect(True)  # removes OS titlebar
        self.root.attributes("-topmost", True)

        # Move window with mouse (since no titlebar)
        self.root.bind("<Button-1>", self.start_move)
        self.root.bind("<B1-Motion>", self.do_move)

        # UI frame
        self.frame = tk.Frame(self.root, bg="black")
        self.frame.pack(padx=10, pady=10)

        self.create_btn = tk.Button(self.frame, text="Create Room", command=self.create_room)
        self.create_btn.pack(pady=5)

        self.join_btn = tk.Button(self.frame, text="Join Room", command=self.join_room)
        self.join_btn.pack(pady=5)

        # Close button (custom, since no title bar)
        self.close_btn = tk.Button(self.frame, text="X", command=self.root.destroy, fg="red", bg="black")
        self.close_btn.pack(side="bottom", pady=5)

        self.room_code = None
        self.websocket = None

        # Start WebSocket in background
        threading.Thread(target=self.start_ws, daemon=True).start()

    def start_move(self, event):
        self.x = event.x
        self.y = event.y

    def do_move(self, event):
        dx = event.x - self.x
        dy = event.y - self.y
        x = self.root.winfo_x() + dx
        y = self.root.winfo_y() + dy
        self.root.geometry(f"+{x}+{y}")

    def hide_buttons(self):
        self.create_btn.pack_forget()
        self.join_btn.pack_forget()

    def create_room(self):
        self.room_code = simpledialog.askstring("Create Room", "Enter new room code:")
        if self.room_code:
            asyncio.run_coroutine_threadsafe(
                self.send_message({"action": "create", "room": self.room_code}), self.loop
            )
            self.hide_buttons()

    def join_room(self):
        self.room_code = simpledialog.askstring("Join Room", "Enter room code:")
        if self.room_code:
            asyncio.run_coroutine_threadsafe(
                self.send_message({"action": "join", "room": self.room_code}), self.loop
            )
            self.hide_buttons()

    async def send_message(self, message: dict):
        if self.websocket:
            try:
                await self.websocket.send(str(message))
            except Exception as e:
                print("Send failed:", e)

    async def ws_handler(self):
        try:
            async with websockets.connect(SERVER_URL) as ws:
                self.websocket = ws
                async for msg in ws:
                    print("Received:", msg)
        except Exception as e:
            print("WebSocket error:", e)
            messagebox.showerror("Connection", f"Lost connection to server:\n{e}")

    def start_ws(self):
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)
        self.loop.run_until_complete(self.ws_handler())

if __name__ == "__main__":
    root = tk.Tk()
    app = RaceLightApp(root)
    root.mainloop()
