import tkinter as tk
import random
import asyncio
import websockets

# Read server URL from local config.txt
with open("config.txt", "r") as f:
    SERVER_URL = f.read().strip()

# Add WebSocket path
WS_URL = f"{SERVER_URL}/ws"

class RaceLightApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Race Light")
        self.root.configure(bg="#222222")
        self.root.attributes("-topmost", True)
        self.root.overrideredirect(True)
        self.root.geometry("180x200")

        self.countdown = 10
        self.is_running = True

        # Close/minimize buttons
        self.close_btn = tk.Button(root, text="X", command=self.root.destroy,
                                   bg="#222222", fg="white", bd=0, highlightthickness=0)
        self.min_btn = tk.Button(root, text="_", command=self.minimize,
                                 bg="#222222", fg="white", bd=0, highlightthickness=0)
        self.close_btn.place_forget()
        self.min_btn.place_forget()

        # Show buttons on hover
        self.root.bind("<Enter>", self.show_buttons)
        self.root.bind("<Leave>", self.hide_buttons)

        # Drag window
        self.root.bind("<Button-1>", self.click_window)
        self.root.bind("<B1-Motion>", self.move_window)
        self.offset_x = 0
        self.offset_y = 0

        # Label for countdown / Be Ready
        self.text_label = tk.Label(root, text="", font=("Arial", 18),
                                   fg="white", bg="#222222")
        self.text_label.pack(pady=10)

        # Canvas for circle
        self.canvas = tk.Canvas(root, width=100, height=100,
                                bg="#222222", highlightthickness=0)
        self.canvas.pack(pady=10)
        self.circle = self.canvas.create_oval(10, 10, 90, 90, fill="grey")

        # Start WebSocket connection
        asyncio.get_event_loop().run_until_complete(self.start_ws())

        # Start the loop automatically
        self.loop_cycle()

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

    # Main loop
    def loop_cycle(self):
        self.countdown = 10
        self.text_label.config(text=f"Next light {self.countdown}")
        self.canvas.itemconfig(self.circle, fill="grey")
        self.countdown_step()

    def countdown_step(self):
        if self.countdown > 0:
            self.countdown -= 1
            self.text_label.config(text=f"Next light {self.countdown}")
            self.root.after(1000, self.countdown_step)
        else:
            self.text_label.config(text="Be Ready")
            self.canvas.itemconfig(self.circle, fill="yellow")
            delay = random.randint(1000, 10000)
            self.root.after(delay, self.show_green)

    def show_green(self):
        self.text_label.config(text="")
        self.canvas.itemconfig(self.circle, fill="green")
        self.root.after(3000, self.loop_cycle)

    # WebSocket connection
    async def start_ws(self):
        try:
            async with websockets.connect(WS_URL) as websocket:
                while True:
                    message = await websocket.recv()
                    # Example: handle messages from server if needed
                    print("Received from server:", message)
        except Exception as e:
            print("WebSocket error:", e)

def main():
    root = tk.Tk()
    app = RaceLightApp(root)
    root.mainloop()

if __name__ == "__main__":
    main()
