import asyncio
import threading
import tkinter as tk
from tkinter import simpledialog
import websockets
import time

def load_config():
    try:
        with open("config.txt", "r") as f:
            for line in f:
                if line.startswith("SERVER_URL="):
                    return line.strip().split("=", 1)[1]
    except FileNotFoundError:
        return "wss://racelightrelay-production.up.railway.app"
SERVER_URL = load_config()


class RaceLightApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Evucy's Anti-Ping")
        self.root.configure(bg="black")
        self.root.overrideredirect(True)
        self.root.attributes("-topmost", True)
        self.root.geometry("250x180")

        # Move window
        self.root.bind("<Button-1>", self.start_move)
        self.root.bind("<B1-Motion>", self.do_move)

        # Title label (top center, smaller)
        self.title_label = tk.Label(root, text="Evucy's Anti-Ping", fg="#555555",
                                    bg="black", font=("Arial", 10, "bold"))
        self.title_label.place(relx=0.5, y=5, anchor="n")

        # Canvas for lights
        self.canvas = tk.Canvas(root, width=250, height=120, bg="black", highlightthickness=0)
        self.canvas.place(x=0, y=30)

        # Close & minimize buttons
        self.close_btn = tk.Button(root, text="X", fg="red", bg="black", bd=0, command=root.destroy)
        self.min_btn = tk.Button(root, text="_", fg="white", bg="black", bd=0, command=self.minimize)
        self.close_btn.place_forget()
        self.min_btn.place_forget()
        self.root.bind("<Enter>", self.show_controls)
        self.root.bind("<Leave>", self.hide_controls)

        # Create / Join room buttons
        self.create_btn = tk.Button(root, text="Create Room", command=self.create_room)
        self.create_btn.place(x=20, y=160, width=100)
        self.join_btn = tk.Button(root, text="Join Room", command=self.join_room)
        self.join_btn.place(x=130, y=160, width=100)

        # Networking
        self.room_code = None
        self.websocket = None
        self.loop = None

        threading.Thread(target=self.start_ws, daemon=True).start()

    # Window move
    def start_move(self, e):
        self.x = e.x
        self.y = e.y

    def do_move(self, e):
        dx = e.x - self.x
        dy = e.y - self.y
        x = self.root.winfo_x() + dx
        y = self.root.winfo_y() + dy
        self.root.geometry(f"+{x}+{y}")

    # Hover buttons
    def show_controls(self, e=None):
        self.close_btn.place(x=225, y=0, width=20, height=20)
        self.min_btn.place(x=200, y=0, width=20, height=20)

    def hide_controls(self, e=None):
        self.close_btn.place_forget()
        self.min_btn.place_forget()

    def minimize(self):
        self.root.iconify()

    # Room buttons
    def create_room(self):
        self.room_code = simpledialog.askstring("Create Room", "Enter new room code:")
        if self.room_code:
            asyncio.run_coroutine_threadsafe(
                self.send_message({"action": "create", "room": self.room_code}), self.loop
            )
            self.create_btn.place_forget()
            self.join_btn.place_forget()

    def join_room(self):
        self.room_code = simpledialog.askstring("Join Room", "Enter room code:")
        if self.room_code:
            asyncio.run_coroutine_threadsafe(
                self.send_message({"action": "join", "room": self.room_code}), self.loop
            )
            self.create_btn.place_forget()
            self.join_btn.place_forget()

    # Update canvas
    def update_circle(self, color=None, text=None):
        self.canvas.delete("all")
        if color:
            self.canvas.create_oval(75, 20, 175, 120, fill=color, outline=color)
        if text:
            self.canvas.create_text(125, 10, text=text, fill="white", font=("Arial", 14, "bold"))

    # Handle server events
    def handle_server_event(self, data):
        ev = data.get("event")
        if ev == "countdown":
            sec = data.get("time", 0)
            self.root.after(0, lambda: self.update_circle(None, f"Next light: {sec}"))
        elif ev == "ready":
            self.root.after(0, lambda: self.update_circle("yellow", "Be ready"))
        elif ev == "green_time":
            # Calculate remaining delay based on server timestamp
            start = data.get("start", time.time())
            delay = data.get("delay", 1)
            elapsed = time.time() - start
            remaining = max(0, delay - elapsed)
            self.root.after(int(remaining * 1000), lambda: self.update_circle("green", None))
        elif ev == "green":
            self.root.after(0, lambda: self.update_circle("green", None))

    async def send_message(self, message: dict):
        if self.websocket:
            import json
            try:
                await self.websocket.send(json.dumps(message))
            except Exception as e:
                print("Send failed:", e)

    async def ws_handler(self):
        import json, time
        while True:
            try:
                async with websockets.connect(SERVER_URL) as ws:
                    self.websocket = ws
                    async for msg in ws:
                        data = json.loads(msg)
                        self.handle_server_event(data)
            except Exception:
                time.sleep(2)

    def start_ws(self):
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)
        self.loop.run_until_complete(self.ws_handler())


if __name__ == "__main__":
    root = tk.Tk()
    app = RaceLightApp(root)
    root.mainloop()
