import tkinter as tk
import asyncio
import websockets
import threading
import json

# Read server URL from config.txt
with open("config.txt", "r") as f:
    SERVER_URI = f.read().strip()


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

    # Update GUI based on server message
    def handle_server_message(self, data):
        if data["type"] == "countdown":
            self.text_label.config(text=f"Next light {data['seconds']}")
            self.canvas.itemconfig(self.circle, fill="grey")
        elif data["type"] == "be_ready":
            self.text_label.config(text="Be Ready")
            self.canvas.itemconfig(self.circle, fill="yellow")
        elif data["type"] == "green":
            self.text_label.config(text="")
            self.canvas.itemconfig(self.circle, fill="green")
        elif data["type"] == "info":
            print(data["text"])  # optional info logging

# Async connection to relay server
async def connect_to_server(app, room_code):
    async with websockets.connect(SERVER_URI) as websocket:
        # Send join room message
        await websocket.send(json.dumps({"action": "join", "room": room_code}))

        while True:
            message = await websocket.recv()
            data = json.loads(message)
            # Update GUI in main thread
            app.root.after(0, app.handle_server_message, data)

# Start asyncio in a thread
def start_async_loop(app, room_code):
    asyncio.new_event_loop().run_until_complete(connect_to_server(app, room_code))

def main():
    room_code = input("Enter 4-digit room code: ")  # could replace with GUI input later
    root = tk.Tk()
    app = RaceLightApp(root)

    threading.Thread(target=start_async_loop, args=(app, room_code), daemon=True).start()
    root.mainloop()

if __name__ == "__main__":
    main()
