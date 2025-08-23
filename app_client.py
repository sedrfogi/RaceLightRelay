import tkinter as tk
import json
import random
import asyncio
import websockets

# Read relay URL from config.txt
with open("config.txt", "r") as f:
    SERVER_URL = f.read().strip()

ROOM_CODE = input("Enter room code: ")  # or generate your own if creating a room

class RaceLightApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Race Light")
        self.root.configure(bg="#222222")
        self.root.attributes("-topmost", True)
        self.root.overrideredirect(True)
        self.root.geometry("180x200")

        self.close_btn = tk.Button(root, text="X", command=self.root.destroy, bg="#222222", fg="white", bd=0, highlightthickness=0)
        self.min_btn = tk.Button(root, text="_", command=self.minimize, bg="#222222", fg="white", bd=0, highlightthickness=0)
        self.close_btn.place_forget()
        self.min_btn.place_forget()
        self.root.bind("<Enter>", self.show_buttons)
        self.root.bind("<Leave>", self.hide_buttons)

        self.offset_x = 0
        self.offset_y = 0
        self.root.bind("<Button-1>", self.click_window)
        self.root.bind("<B1-Motion>", self.move_window)

        self.text_label = tk.Label(root, text="", font=("Arial", 14), fg="white", bg="#222222")
        self.text_label.pack(pady=10)

        self.canvas = tk.Canvas(root, width=100, height=100, bg="#222222", highlightthickness=0)
        self.canvas.pack(pady=10)
        self.circle = self.canvas.create_oval(10, 10, 90, 90, fill="grey")

        # Start asyncio WebSocket listener
        asyncio.ensure_future(self.listen_to_server())

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

    async def listen_to_server(self):
        async with websockets.connect(f"{SERVER_URL}/ws/{ROOM_CODE}") as websocket:
            while True:
                data = await websocket.recv()
                msg = json.loads(data)
                if msg["type"] == "countdown":
                    self.text_label.config(text=f"Next light {msg['value']}")
                    self.canvas.itemconfig(self.circle, fill="grey")
                elif msg["type"] == "be_ready":
                    self.text_label.config(text="Be Ready")
                    self.canvas.itemconfig(self.circle, fill="yellow")
                elif msg["type"] == "green":
                    self.text_label.config(text="")
                    self.canvas.itemconfig(self.circle, fill="green")
                    await asyncio.sleep(3)
                    self.text_label.config(text="")
                    self.canvas.itemconfig(self.circle, fill="grey")

def main():
    root = tk.Tk()
    app = RaceLightApp(root)
    loop = asyncio.get_event_loop()
    loop.create_task(asyncio.sleep(0))  # start asyncio
    loop.run_until_complete(asyncio.ensure_future(asyncio.sleep(0)))
    root.mainloop()

if __name__ == "__main__":
    main()
