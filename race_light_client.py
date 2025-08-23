import tkinter as tk
import asyncio
import websockets
import json

# Read server URL from config.txt
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

        # Label and canvas
        self.text_label = tk.Label(root, text="", font=("Arial", 18),
                                   fg="white", bg="#222222")
        self.text_label.pack(pady=10)

        self.canvas = tk.Canvas(root, width=100, height=100,
                                bg="#222222", highlightthickness=0)
        self.canvas.pack(pady=10)
        self.circle = self.canvas.create_oval(10, 10, 90, 90, fill="grey")

        # Start websocket loop
        self.loop = asyncio.get_event_loop()
        self.loop.create_task(self.connect_ws())
        self.run_loop()

    # Hover / drag / minimize functions
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

    # WebSocket connection
    async def connect_ws(self):
        try:
            async with websockets.connect(SERVER_URL) as ws:
                async for message in ws:
                    data = json.loads(message)
                    self.update_light(data)
        except Exception as e:
            print("WebSocket error:", e)
            self.root.after(2000, lambda: self.loop.create_task(self.connect_ws()))

    # Update UI from server
    def update_light(self, data):
        state = data.get("state")
        if state == "grey":
            self.text_label.config(text=f"Next light {data.get('countdown', 10)}")
            self.canvas.itemconfig(self.circle, fill="grey")
        elif state == "yellow":
            self.text_label.config(text="Be Ready")
            self.canvas.itemconfig(self.circle, fill="yellow")
        elif state == "green":
            self.text_label.config(text="")
            self.canvas.itemconfig(self.circle, fill="green")

    # Run asyncio loop inside Tkinter
    def run_loop(self):
        try:
            self.loop.run_until_complete(asyncio.sleep(0.1))
        except:
            pass
        self.root.after(50, self.run_loop)

def main():
    root = tk.Tk()
    app = RaceLightApp(root)
    root.mainloop()

if __name__ == "__main__":
    main()
