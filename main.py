import os
import tkinter as tk
import numpy as np
from PIL import Image, ImageTk
from tkinter import filedialog, messagebox
import struct

class GameOfLife:
    def __init__(self, master):
        self.master = master
        self.cell_size = 10
        self.canvas_size = 1500
        self.cols = self.canvas_size // self.cell_size
        self.rows = self.canvas_size // self.cell_size
        self.running = False
        self.grid = np.zeros((self.rows, self.cols), dtype=int)

        icon_dir = os.path.join(os.path.dirname(__file__), 'icons')

        self.play_icon = ImageTk.PhotoImage(Image.open(os.path.join(icon_dir, "play.ico")).resize((24, 24)))
        self.pause_icon = ImageTk.PhotoImage(Image.open(os.path.join(icon_dir, "pause.ico")).resize((24, 24)))
        self.step_icon = ImageTk.PhotoImage(Image.open(os.path.join(icon_dir, "forward.ico")).resize((24, 24)))
        self.pencil_icon = ImageTk.PhotoImage(Image.open(os.path.join(icon_dir, "pencil.ico")).resize((24, 24)))
        self.rubber_icon = ImageTk.PhotoImage(Image.open(os.path.join(icon_dir, "rubber.ico")).resize((24, 24)))
        self.nuke_icon = ImageTk.PhotoImage(Image.open(os.path.join(icon_dir, "nuke.ico")).resize((24, 24)))

        window_icon = Image.open(os.path.join(icon_dir, "icon.ico")).resize((64, 64), Image.NEAREST)
        self.master.iconphoto(True, ImageTk.PhotoImage(window_icon))

        self.master.title("Glide")

        menubar = tk.Menu(master)
        self.master.config(menu=menubar)

        file_menu = tk.Menu(menubar, tearoff=0)
        file_menu.add_command(label="Open", command=self.open_file, accelerator="CTRL+O")
        file_menu.add_command(label="Save", command=self.save_file, accelerator="CTRL+S")
        file_menu.add_command(label="Exit", command=self.master.quit)
        menubar.add_cascade(label="File", menu=file_menu)

        edit_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Edit", menu=edit_menu)

        self.toolbar = tk.Frame(master, bg='gray', height=30)
        self.toolbar.pack(fill=tk.X)

        self.create_toolbar_buttons()

        self.canvas_frame = tk.Frame(master)
        self.canvas_frame.pack(padx=5, pady=5, fill=tk.BOTH, expand=True)

        self.canvas = tk.Canvas(self.canvas_frame, width=self.canvas_size, height=self.canvas_size, bg='#2b2b2b')
        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        self.v_scrollbar = tk.Scrollbar(self.canvas_frame, orient=tk.VERTICAL, command=self.canvas.yview)
        self.h_scrollbar = tk.Scrollbar(self.canvas_frame, orient=tk.HORIZONTAL, command=self.canvas.xview)

        self.canvas.configure(yscrollcommand=self.v_scrollbar.set, xscrollcommand=self.h_scrollbar.set)

        self.v_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.h_scrollbar.pack(side=tk.BOTTOM, fill=tk.X)

        self.scrollable_frame = tk.Frame(self.canvas)
        self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")

        self.canvas.bind("<Configure>", self.on_canvas_configure)

        self.draw_grid()

        self.canvas.bind("<Button-1>", self.start_drawing)
        self.canvas.bind("<B1-Motion>", self.draw)
        self.canvas.bind("<ButtonRelease-1>", self.stop_drawing)

        self.drawing = False
        self.last_x, self.last_y = None, None

        self.master.bind('<Return>', lambda e: self.toggle())
        self.master.bind('p', lambda e: self.use_pencil_tool())
        self.master.bind('r', lambda e: self.use_eraser_tool())
        self.master.bind('<Control-o>', lambda e: self.open_file())
        self.master.bind('<Control-s>', lambda e: self.save_file())

        self.update_canvas()

    def create_toolbar_buttons(self):
        self.toggle_button = tk.Button(
            self.toolbar,
            image=self.play_icon,
            command=self.toggle,
            bg='lightgray',
            bd=0,
            activebackground='gray'
        )
        self.toggle_button.pack(side=tk.LEFT, padx=5)

        self.step_button = tk.Button(
            self.toolbar,
            image=self.step_icon,
            command=self.step_simulation,
            bg='lightgray',
            bd=0,
            activebackground='gray'
        )
        self.step_button.pack(side=tk.LEFT, padx=5)

        self.pencil_button = tk.Button(
            self.toolbar,
            image=self.pencil_icon,
            command=self.use_pencil_tool,
            bg='lightgray',
            bd=0,
            activebackground='gray'
        )
        self.pencil_button.pack(side=tk.LEFT, padx=5)

        self.rubber_button = tk.Button(
            self.toolbar,
            image=self.rubber_icon,
            command=self.use_eraser_tool,
            bg='lightgray',
            bd=0,
            activebackground='gray'
        )
        self.rubber_button.pack(side=tk.LEFT, padx=5)

        self.nuke_button = tk.Button(
            self.toolbar,
            image=self.nuke_icon,
            command=self.clear_grid,
            bg='lightgray',
            bd=0,
            activebackground='gray'
        )
        self.nuke_button.pack(side=tk.LEFT, padx=5)

        self.speed_slider = tk.Scale(
            self.toolbar,
            from_=1,
            to=20,
            orient=tk.HORIZONTAL,
            length=200,
            bg='lightgray',
            activebackground='gray',
            label="Speed (1 = 0.25s, 20 = 0.0125s)"
        )
        self.speed_slider.set(1)
        self.speed_slider.pack(side=tk.RIGHT, padx=5)

    def draw_grid(self):
        for i in range(self.rows):
            self.canvas.create_line(0, i * self.cell_size, self.canvas_size, i * self.cell_size, fill='black')
        for j in range(self.cols):
            self.canvas.create_line(j * self.cell_size, 0, j * self.cell_size, self.canvas_size, fill='black')

    def on_canvas_configure(self, event):
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))

    def toggle(self):
        self.running = not self.running
        if self.running:
            self.toggle_button.config(image=self.pause_icon)
            self.run_simulation()
        else:
            self.toggle_button.config(image=self.play_icon)

    def step_simulation(self):
        self.update_grid()
        self.update_canvas()
    
    def run_simulation(self):
       if self.running:
            self.update_grid()
            self.update_canvas()
            self.master.after(250 // self.speed_slider.get(), self.run_simulation)

    def use_pencil_tool(self):
        self.drawing = True

    def use_eraser_tool(self):
        self.drawing = False

    def start_drawing(self, event):
        self.last_x, self.last_y = event.x, event.y
        self.draw(event)

    def draw(self, event):
        x, y = event.x // self.cell_size, event.y // self.cell_size

        if self.drawing:
            if self.last_x is not None and self.last_y is not None:
                self.draw_line(self.last_x, self.last_y, event.x, event.y)
            if 0 <= x < self.cols and 0 <= y < self.rows:
                self.grid[y, x] = 1
                self.draw_cell(x, y)

        else:
            if 0 <= x < self.cols and 0 <= y < self.rows:
                self.grid[y, x] = 0
                self.clear_cell(x, y)

        self.last_x, self.last_y = event.x, event.y

    def stop_drawing(self, event):
        self.last_x, self.last_y = None, None

    def draw_line(self, x1, y1, x2, y2):
        pass

    def draw_cell(self, x, y):
        x1 = x * self.cell_size
        y1 = y * self.cell_size
        x2 = x1 + self.cell_size
        y2 = y1 + self.cell_size
        self.canvas.create_rectangle(x1, y1, x2, y2, fill="white", outline="black")

    def clear_cell(self, x, y):
        x1 = x * self.cell_size
        y1 = y * self.cell_size
        x2 = x1 + self.cell_size
        y2 = y1 + self.cell_size
        self.canvas.create_rectangle(x1, y1, x2, y2, fill="#2b2b2b", outline="black")

    def update_canvas(self):
        self.canvas.delete("all")
        self.draw_grid()
        for y in range(self.rows):
            for x in range(self.cols):
                if self.grid[y, x] == 1:
                    self.draw_cell(x, y)

    def update_grid(self):
        new_grid = np.copy(self.grid)
        for row in range(self.rows):
            for col in range(self.cols):
                live_neighbors = self.count_live_neighbors(row, col)
                if self.grid[row, col] == 1:
                    if live_neighbors < 2 or live_neighbors > 3:
                        new_grid[row, col] = 0
                elif live_neighbors == 3:
                    new_grid[row, col] = 1
        self.grid = new_grid

    def count_live_neighbors(self, row, col):
        total = 0
        for i in range(-1, 2):
            for j in range(-1, 2):
                r, c = row + i, col + j
                if (0 <= r < self.rows and 0 <= c < self.cols) and not (i == 0 and j == 0):
                    total += self.grid[r, c]
        return total

    def open_file(self):
        file_path = filedialog.askopenfilename(defaultextension=".rle", filetypes=[("Run Length Encoded", "*.rle"), ("All Files", "*.*")])
        if file_path:
            with open(file_path, "r") as file:
                data = file.readlines()
            # Load RLE file here

    def save_file(self):
        file_path = filedialog.asksaveasfilename(defaultextension=".rle", filetypes=[("Run Length Encoded", "*.rle"), ("All Files", "*.*")])
        if file_path:
            with open(file_path, "w") as file:
                # Save grid to RLE format

    def clear_grid(self):
        self.grid = np.zeros((self.rows, self.cols), dtype=int)
        self.update_canvas()

if __name__ == "__main__":
    root = tk.Tk()
    app = GameOfLife(root)
    root.mainloop()
