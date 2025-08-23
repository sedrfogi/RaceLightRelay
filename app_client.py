import tkinter as tk
import asyncio
import json
import websockets

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

        # Custom close/minimize buttons
        self.close_btn = tk.Button(root, text="X", command=self.root.destroy,
                                   bg="#222222", fg="white", bd=0, highlightthickness=0)
        self.min_btn = tk.Button(root, text="_", command=self.minimize,
                                 bg="#222222", fg="white", bd=0, highlightthickness=0)
        self.close_btn.place_forget()
        self.min_btn.place_forget()

        self.root.bind("<Enter>", self.show_buttons)
        self.root.bind("<Leave>", self.hide_buttons)
        self.root.bind("<Button-1>", self.click_window)
        self.root.bind("<B1-Motion>", self.move_window)
        self.offset_x = 0
        self.offset_y = 0

        # Label and Canvas
        self.text_label = tk.Label(root, text="", font=("Arial", 18), fg="white", bg="#222222")
        self.text_label.pack(pady=10)
        self.canvas = tk.Canvas(root, width=100, height=100, bg="#222222", highlightthickness=0)
        self.canvas.pack(pady=10)
        self.circle = self.canvas.create_oval(10, 10, 90, 90, fill="grey")

        # Start asyncio loop for WebSocket
        self.loop = asyncio.get_event_loop()
        self.loop.create_task(self.websocket_handler())
        self.loop.create_task(self.update_loop())
        self.loop.run_until_complete(asyncio.sleep(0))  # Start tasks

    # Hover & drag
    def show_buttons(self, event=None):
        self.close_btn.place(x=150, y=0, width=30, height=20)
        self.min_btn.place(x=120, y=0, width=30, height=20)
    def hide_buttons(self, event=None):
        self.close_btn.place_forget()
        self.min_btn.place_forget()
    def click_window(self, event):
        self.offset_x = event.x
        self.offset_y = event.y
    def move_window(self, event):
        x = event.x_root - self.offset_x
        y = event.y_root - self.offset_y
        self.root.geometry(f"+{x}+{y}")
    def minimize(self):
        self.root.iconify()

    # Countdown loop
    async def update_loop(self):
        while True:
            await asyncio.sleep(0.1)
            self.root.update()

    # WebSocket communication
    async def websocket_handler(self):
        async with websockets.connect(SERVER_URL) as ws:
            self.ws = ws
            # Send join message
            await ws.send(json.dumps({"type": "join"}))
            async for message in ws:
                data = json.loads(message)
                if data["type"] == "countdown":
                    self.countdown = data["value"]
                    self.text_label.config(text=f"Next light {self.countdown}")
                    self.canvas.itemconfig(self.circle, fill="grey")
                elif data["type"] == "yellow":
                    self.text_label.config(text="Be Ready")
                    self.canvas.itemconfig(self.circle, fill="yellow")
                elif data["type"] == "green":
                    self.text_label.config(text="")
                    self.canvas.itemconfig(self.circle, fill="green")

def main():
    root = tk.Tk()
    app = RaceLightApp(root)
    root.mainloop()

if __name__ == "__main__":
    main()
