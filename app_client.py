import tkinter as tk
import random

# Read server URL from local config.txt
with open("config.txt", "r") as f:
    SERVER_URL = f.read().strip()

class RaceLightApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Race Light")
        self.root.configure(bg="#222222")
        self.root.attributes("-topmost", True)  # always on top
        self.root.overrideredirect(True)  # borderless window
        self.root.geometry("180x200")  # small compact size

        self.countdown = 10
        self.is_running = True

        # Custom close/minimize buttons
        self.close_btn = tk.Button(root, text="X", command=self.root.destroy,
                                   bg="#222222", fg="white", bd=0, highlightthickness=0)
        self.min_btn = tk.Button(root, text="_", command=self.minimize,
                                 bg="#222222", fg="white", bd=0, highlightthickness=0)
        self.close_btn.place_forget()
        self.min_btn.place_forget()

        # Show buttons on hover anywhere
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
            # Be Ready
            self.text_label.config(text="Be Ready")
            self.canvas.itemconfig(self.circle, fill="yellow")
            delay = random.randint(1000, 10000)
            self.root.after(delay, self.show_green)

    def show_green(self):
        self.text_label.config(text="")
        self.canvas.itemconfig(self.circle, fill="green")
        self.root.after(3000, self.loop_cycle)

def main():
    root = tk.Tk()
    app = RaceLightApp(root)
    root.mainloop()

if __name__ == "__main__":
    main()
