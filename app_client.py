import tkinter as tk
import asyncio
import websockets
import json
import threading

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
        self.current_light = "grey"

        # Buttons
        self.close_btn = tk.Button(root, text="X", command=self.root.destroy,
                                   bg="#222222", fg="white", bd=0, highlightthickness=0)
        self.min_btn = tk.Button(root, text="_", command=self.minimize,
                                 bg="#222222", fg="white", bd=0, highlightthickness=0)
        self.close_btn.place_forget()
        self.min_btn.place_forget()

        self.root.bind("<Enter>", self.show_buttons)
        self.root.bind("<Leave>", self.hide_buttons)

        # Drag
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

        # Start WebSocket in separate thread
        threading.Thread(target=self.start_ws_loop, daemon=True).start()

    # Hover functions
    def show_buttons(self, event=None):
        self.close_btn.place(x=150, y=0, width=30, height=20)
        self.min_btn.place(x=120, y=0, width=30, height=20)

    def hide_buttons(self, event=None):
        self.close_btn.place_forget()
        self.min_btn.place_forget()

    # Drag functions
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

    # Update light based on server message
    def update_light(self, color, text=""):
        self.current_light = color
        self.canvas.itemconfig(self.circle, fill=color)
        self.text_label.config(text=text)

    # Start asyncio loop for WebSocket
    def start_ws_loop(self):
        asyncio.run(self.ws_loop())

    async def ws_loop(self):
        async with websockets.connect(SERVER_URL) as websocket:
            while True:
                try:
                    message = await websocket.recv()
                    data = json.loads(message)
                    color = data.get("color", "grey")
                    text = data.get("text", "")
                    # Schedule the update on the Tkinter main thread
                    self.root.after(0, self.update_light, color, text)
                except Exception as e:
                    print("WebSocket error:", e)
                    break

def main():
    root = tk.Tk()
    app = RaceLightApp(root)
    root.mainloop()

if __name__ == "__main__":
    main()
