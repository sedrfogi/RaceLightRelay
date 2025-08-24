# lights_client.py
import asyncio
import json
import threading
import tkinter as tk
from tkinter import simpledialog, messagebox
import websockets
import os
import re
from pathlib import Path

"""
Client UI:
- Two buttons: Create Room, Join Room
- Always-on-top frameless window; draggable
- Canvas draws a big circle + status text

Networking:
- Reads SERVER_URL from config.txt (same folder). Example:
    SERVER_URL=ws://your-railway-app.up.railway.app
  Use wss:// if Railway is HTTPS only.
- JSON-only protocol
- Auto-reconnect on errors
"""

CONFIG_FILE = Path(__file__).with_name("config.txt")

def load_server_url() -> str:
    # default fallback (local dev)
    default = "ws://localhost:8080"
    if not CONFIG_FILE.exists():
        return default
    try:
        for line in CONFIG_FILE.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            m = re.match(r"SERVER_URL\s*=\s*(\S+)", line, flags=re.IGNORECASE)
            if m:
                return m.group(1)
    except Exception:
        pass
    return default

SERVER_URL = load_server_url()


class RaceLightApp:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("Race Light Sync")
        self.root.configure(bg="black")
        self.root.overrideredirect(True)   # no OS titlebar
        self.root.attributes("-topmost", True)

        # Window size and starting position
        self.width, self.height = 360, 220
        self.root.geometry(f"{self.width}x{self.height}+200+200")

        # Drag to move
        self._drag_x = 0
        self._drag_y = 0
        self.root.bind("<Button-1>", self._start_move)
        self.root.bind("<B1-Motion>", self._do_move)

        # UI
        self.frame = tk.Frame(self.root, bg="black")
        self.frame.pack(fill="both", expand=True, padx=10, pady=10)

        # Top row: Room controls
        self.btn_row = tk.Frame(self.frame, bg="black")
        self.btn_row.pack(pady=6)
        self.create_btn = tk.Button(self.btn_row, text="Create Room", command=self.create_room)
        self.create_btn.pack(side="left", padx=6)
        self.join_btn = tk.Button(self.btn_row, text="Join Room", command=self.join_room)
        self.join_btn.pack(side="left", padx=6)

        # Status label (server URL + room)
        self.status_lbl = tk.Label(self.frame, text=f"Server: {SERVER_URL}", fg="gray", bg="black")
        self.status_lbl.pack()

        # Canvas for circle + big text
        self.canvas = tk.Canvas(self.frame, width=self.width - 40, height=120, bg="black", highlightthickness=0)
        self.canvas.pack(pady=8)

        # Close button
        self.close_btn = tk.Button(self.frame, text="X", command=self.root.destroy, fg="red", bg="black")
        self.close_btn.pack(side="bottom", pady=5)

        # Drawing ids
        self.circle_id = None
        self.text_id = None

        # Networking
        self.room_code = None
        self.websocket = None
        self.loop = None
        self.stop_event = threading.Event()

        # Start WebSocket background thread
        threading.Thread(target=self._ws_thread, daemon=True).start()

        # Initial UI
        self._render_text("Welcome", color="white")

    # ----- Window movement -----
    def _start_move(self, e):
        self._drag_x = e.x
        self._drag_y = e.y

    def _do_move(self, e):
        dx = e.x - self._drag_x
        dy = e.y - self._drag_y
        x = self.root.winfo_x() + dx
        y = self.root.winfo_y() + dy
        self.root.geometry(f"+{x}+{y}")

    # ----- Buttons -----
    def _validate_room(self, s: str) -> str | None:
        s = (s or "").strip()
        if re.fullmatch(r"\d{4}", s):
            return s
        messagebox.showerror("Room", "Enter a 4-digit code (e.g., 1234).")
        return None

    def create_room(self):
        code = simpledialog.askstring("Create Room", "Enter new 4-digit room code:")
        code = self._validate_room(code)
        if not code:
            return
        self.room_code = code
        self._send_async({"action": "create", "room": code})
        self._on_joined_ui()

    def join_room(self):
        code = simpledialog.askstring("Join Room", "Enter 4-digit room code:")
        code = self._validate_room(code)
        if not code:
            return
        self.room_code = code
        self._send_async({"action": "join", "room": code})
        self._on_joined_ui()

    def _on_joined_ui(self):
        self.create_btn.pack_forget()
        self.join_btn.pack_forget()
        self.status_lbl.config(text=f"Server: {SERVER_URL} | Room: {self.room_code}")

    # ----- Drawing helpers (must run in main thread) -----
    def _render_text(self, msg: str, color: str = "white"):
        if self.text_id is None:
            self.text_id = self.canvas.create_text(
                (self.width - 40) // 2, 25, text=msg, fill=color, font=("Arial", 18, "bold")
            )
        else:
            self.canvas.itemconfigure(self.text_id, text=msg, fill=color)

    def _render_circle(self, color: str | None):
        # Clear old circle
        if self.circle_id is not None:
            self.canvas.delete(self.circle_id)
            self.circle_id = None

        if not color:
            return

        w = self.width - 40
        cx, cy = w // 2, 85
        r = 40
        self.circle_id = self.canvas.create_oval(cx - r, cy - r, cx + r, cy + r, fill=color, outline=color)

    # ----- Server event handler (schedule UI updates with root.after) -----
    def handle_server_event(self, data: dict):
        t = data.get("type")
        if t == "info":
            msg = data.get("message", "")
            self.root.after(0, lambda: self._render_text(msg, "white"))
            return

        if t == "state":
            ev = data.get("event")
            if ev == "countdown":
                sec = data.get("time", 0)
                self.root.after(0, lambda: (self._render_text(f"Next light {sec}", "white"),
                                             self._render_circle(None)))
            elif ev == "ready":
                self.root.after(0, lambda: (self._render_text("Be ready", "yellow"),
                                             self._render_circle("yellow")))
            elif ev == "green":
                self.root.after(0, lambda: (self._render_text("GO!", "green"),
                                             self._render_circle("green")))

    # ----- Networking (async) -----
    async def _connect_and_listen(self):
        while not self.stop_event.is_set():
            try:
                async with websockets.connect(SERVER_URL, ping_interval=20, ping_timeout=20) as ws:
                    self.websocket = ws
                    # If we already chose room, re-send our intent (helps on reconnect)
                    if self.room_code:
                        action = {"action": "join", "room": self.room_code}
                        await ws.send(json.dumps(action))

                    async for raw in ws:
                        try:
                            data = json.loads(raw)
                        except json.JSONDecodeError:
                            continue
                        self.handle_server_event(data)

            except Exception as e:
                # Show a small connection status; then retry
                self.root.after(0, lambda: self._render_text(f"Reconnecting...", "gray"))
                await asyncio.sleep(3)

    def _ws_thread(self):
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)
        try:
            self.loop.run_until_complete(self._connect_and_listen())
        finally:
            self.loop.close()

    def _send_async(self, message: dict):
        # Thread-safe: schedule a coroutine on the WS loop
        async def _send():
            if self.websocket is None:
                return
            try:
                await self.websocket.send(json.dumps(message))
            except Exception as e:
                print("Send failed:", e)

        if self.loop and self.loop.is_running():
            asyncio.run_coroutine_threadsafe(_send(), self.loop)

    # ----- Cleanup -----
    def close(self):
        self.stop_event.set()
        self.root.destroy()


if __name__ == "__main__":
    root = tk.Tk()
    app = RaceLightApp(root)
    root.protocol("WM_DELETE_WINDOW", app.close)
    root.mainloop()
