import tkinter as tk
import asyncio
import websockets
import json
import random

# Read server URL from local config.txt
with open("config.txt", "r") as f:
    SERVER_URL = f.read().strip()

class RaceLightApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Race Light")
        self.root.configure(bg="#222222")
        self.root.attributes("-topmost", True)
        self.root.overrideredirect(True)
        self.root.geometry("180x200")

        self.countdown = 10
        self.is_in_room = False

        # Close/Minimize buttons
        self.close_btn = tk.Button(root, text="X", command=self.root.destroy,
                                   bg="#222222", fg="white", bd=0, highlightthickness=0)
        self.min_btn = tk.Button(root, text="_", command=self.minimize,
                                 bg="#222222", fg="white", bd=0, highlightthickness=0)
        self.close_btn.place_forget()
        self.min_btn.place_forget()

        # Hover buttons
        self.root.bind("<Enter>", self.show_buttons)
        self.root.bind("<Leave>", self.hide_buttons)

        # Dragging
        self.root.bind("<Button-1>", self.click_window)
        self.root.bind("<B1-Motion>", self.move_window)
        self.offset_x = 0
        self.offset_y = 0

        # Countdown label
        self.text_label = tk.Label(root, text="", font=("Arial", 18),
                                   fg="white", bg="#222222")
        self.text_label.pack(pady=10)

        # Canvas for lights
        self.canvas = tk.Canvas(root, width=100, height=100,
                                bg="#222222", highlightthickness=0)
        self.canvas.pack(pady=10)
        self.circle = self.canvas.create_oval(10, 10, 90, 90, fill="grey")

        # Create/Join buttons
        self.create_btn = tk.Button(root, text="Create Room", command=self.create_room,
                                    bg="#444", fg="white")
        self.join_btn = tk.Button(root, text="Join Room", command=self.join_room,
                                  bg="#444", fg="white")
        self.create_btn.pack(pady=5)
        self.join_btn.pack(pady=5)

        # Start websocket loop
        self.loop = asyncio.get_event_loop()
        self.loop.create_task(self.start_ws())

    # Hover functions
    def show_buttons(self, event=None):
        self.close_btn.place(x=150, y=0, width=30, height=20)
        self.min_btn.place(x=120, y=0, width=30, height=20)

    def hide_buttons(self, event=None):
        self.close_btn.place_forget()
        self.min_btn.place_forget()

    # Dragging functions
    def click_window(self, event):
        self.offset_x = event.x
        self.offset_y = event.y

    def move_window(self, event):
        x = event.x_root - self.offset_x
        y = event.y_root - self.offset_y
        self.root.geometry(f"+{x}+{y}")

    # Minimize
    def minimize(self):
        self.root.iconify()

    # Room buttons
    def create_room(self):
        if self.websocket:
            asyncio.create_task(self.send_message({"action": "create_room"}))

    def join_room(self):
        if self.websocket:
            asyncio.create_task(self.send_message({"action": "join_room"}))

    # WebSocket
    async def start_ws(self):
        self.websocket = await websockets.connect(SERVER_URL)
        await self.listen_server()

    async def send_message(self, message):
        await self.websocket.send(json.dumps(message))

    async def listen_server(self):
        async for msg in self.websocket:
            data = json.loads(msg)
            if data.get("type") == "room_joined":
                self.is_in_room = True
                self.create_btn.pack_forget()
                self.join_btn.pack_forget()
                self.loop.create_task(self.light_loop())
            elif data.get("type") == "light_update":
                color = data.get("color", "grey")
                self.canvas.itemconfig(self.circle, fill=color)
                self.text_label.config(text=data.get("text", ""))

    async def light_loop(self):
        while self.is_in_room:
            # Countdown
            for i in reversed(range(1, 11)):
                self.text_label.config(text=f"Next light {i}")
                self.canvas.itemconfig(self.circle, fill="grey")
                await asyncio.sleep(1)
            self.text_label.config(text="Be Ready")
            self.canvas.itemconfig(self.circle, fill="yellow")
            delay = random.randint(1, 10)
            await asyncio.sleep(delay)
            self.canvas.itemconfig(self.circle, fill="green")
            self.text_label.config(text="")
            await asyncio.sleep(3)

def main():
    root = tk.Tk()
    app = RaceLightApp(root)
    root.mainloop()

if __name__ == "__main__":
    main()
