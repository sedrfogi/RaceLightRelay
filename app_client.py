import tkinter as tk
import asyncio
import json
import websockets

# Read server URL from config.txt
with open("config.txt", "r") as f:
    SERVER_URL = f.read().strip()  # Example: wss://racelightrelay-production.up.railway.app

class RaceLightApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Race Light")
        self.root.configure(bg="#222222")
        self.root.attributes("-topmost", True)
        self.root.overrideredirect(True)
        self.root.geometry("180x200")

        self.text_label = tk.Label(root, text="", font=("Arial", 18), fg="white", bg="#222222")
        self.text_label.pack(pady=10)

        self.canvas = tk.Canvas(root, width=100, height=100, bg="#222222", highlightthickness=0)
        self.canvas.pack(pady=10)
        self.circle = self.canvas.create_oval(10, 10, 90, 90, fill="grey")

        asyncio.create_task(self.connect_to_server())

    async def connect_to_server(self):
        async with websockets.connect(SERVER_URL) as websocket:
            async for message in websocket:
                state = json.loads(message)
                self.update_ui(state)

    def update_ui(self, state):
        phase = state["phase"]
        countdown = state.get("countdown", 0)
        if phase == "waiting":
            self.text_label.config(text=f"Next light {countdown}")
            self.canvas.itemconfig(self.circle, fill="grey")
        elif phase == "yellow":
            self.text_label.config(text="Be Ready")
            self.canvas.itemconfig(self.circle, fill="yellow")
        elif phase == "green":
            self.text_label.config(text="")
            self.canvas.itemconfig(self.circle, fill="green")

def main():
    root = tk.Tk()
    app = RaceLightApp(root)

    # Start asyncio event loop in Tkinter
    asyncio.get_event_loop().run_until_complete(asyncio.sleep(0))
    async def loop():
        while True:
            await asyncio.sleep(0.1)
    asyncio.get_event_loop().create_task(loop())

    root.mainloop()

if __name__ == "__main__":
    main()
