import os
import tkinter as tk
import numpy as np
from PIL import Image, ImageTk
from tkinter import filedialog, messagebox
import struct  # To help with binary file operations

class GameOfLife:
    def __init__(self, master):
        self.master = master
        self.cell_size = 10
        self.canvas_size = 1500  # Canvas size is 1500x1500
        self.cols = self.canvas_size // self.cell_size
        self.rows = self.canvas_size // self.cell_size
        self.running = False
        self.grid = np.zeros((self.rows, self.cols), dtype=int)

        # Set the directory for icons
        icon_dir = os.path.join(os.path.dirname(__file__), 'icons')

        # Load the toolbar icons
        self.play_icon = ImageTk.PhotoImage(Image.open(os.path.join(icon_dir, "play.ico")).resize((24, 24)))
        self.pause_icon = ImageTk.PhotoImage(Image.open(os.path.join(icon_dir, "pause.ico")).resize((24, 24)))
        self.step_icon = ImageTk.PhotoImage(Image.open(os.path.join(icon_dir, "forward.ico")).resize((24, 24)))
        self.pencil_icon = ImageTk.PhotoImage(Image.open(os.path.join(icon_dir, "pencil.ico")).resize((24, 24)))
        self.rubber_icon = ImageTk.PhotoImage(Image.open(os.path.join(icon_dir, "rubber.ico")).resize((24, 24)))
        self.nuke_icon = ImageTk.PhotoImage(Image.open(os.path.join(icon_dir, "nuke.ico")).resize((24, 24)))

        # Load the window/taskbar icon
        window_icon = Image.open(os.path.join(icon_dir, "icon.ico")).resize((64, 64), Image.NEAREST)
        self.master.iconphoto(True, ImageTk.PhotoImage(window_icon))

        # Set the window title
        self.master.title("Glide")

        # Create the menu bar
        menubar = tk.Menu(master)
        self.master.config(menu=menubar)

        # Create the File menu
        file_menu = tk.Menu(menubar, tearoff=0)
        file_menu.add_command(label="Open", command=self.open_file, accelerator="CTRL+O")
        file_menu.add_command(label="Save", command=self.save_file, accelerator="CTRL+S")
        file_menu.add_command(label="Exit", command=self.master.quit)
        menubar.add_cascade(label="File", menu=file_menu)

        # Create the Edit menu
        edit_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Edit", menu=edit_menu)

        # Create the toolbar
        self.toolbar = tk.Frame(master, bg='gray', height=30)
        self.toolbar.pack(fill=tk.X)

        # Create toolbar buttons
        self.create_toolbar_buttons()

        # Create a frame for the canvas and scrollbars
        self.canvas_frame = tk.Frame(master)
        self.canvas_frame.pack(padx=5, pady=5, fill=tk.BOTH, expand=True)

        # Create the canvas for the simulation
        self.canvas = tk.Canvas(self.canvas_frame, width=self.canvas_size, height=self.canvas_size, bg='#2b2b2b')
        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # Create scrollbars
        self.v_scrollbar = tk.Scrollbar(self.canvas_frame, orient=tk.VERTICAL, command=self.canvas.yview)
        self.h_scrollbar = tk.Scrollbar(self.canvas_frame, orient=tk.HORIZONTAL, command=self.canvas.xview)

        self.canvas.configure(yscrollcommand=self.v_scrollbar.set, xscrollcommand=self.h_scrollbar.set)

        # Pack the scrollbars
        self.v_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.h_scrollbar.pack(side=tk.BOTTOM, fill=tk.X)

        # Create a frame to contain the canvas
        self.scrollable_frame = tk.Frame(self.canvas)
        self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")

        # Set the scroll region of the canvas
        self.canvas.bind("<Configure>", self.on_canvas_configure)

        # Draw the grid
        self.draw_grid()

        # Bind mouse events
        self.canvas.bind("<Button-1>", self.start_drawing)
        self.canvas.bind("<B1-Motion>", self.draw)
        self.canvas.bind("<ButtonRelease-1>", self.stop_drawing)

        # Set initial drawing state
        self.drawing = False
        self.last_x, self.last_y = None, None

        # Set up keybindings
        self.master.bind('<Return>', lambda e: self.toggle())
        self.master.bind('p', lambda e: self.use_pencil_tool())
        self.master.bind('r', lambda e: self.use_eraser_tool())
        self.master.bind('<Control-o>', lambda e: self.open_file())
        self.master.bind('<Control-s>', lambda e: self.save_file())

        # Initialize the simulation
        self.update_canvas()

    def create_toolbar_buttons(self):
        """Create buttons for the toolbar."""
        # Create the play/pause button
        self.toggle_button = tk.Button(
            self.toolbar,
            image=self.play_icon,
            command=self.toggle,
            bg='lightgray',
            bd=0,
            activebackground='gray'
        )
        self.toggle_button.pack(side=tk.LEFT, padx=5)

        # Create the step button
        self.step_button = tk.Button(
            self.toolbar,
            image=self.step_icon,
            command=self.step_simulation,
            bg='lightgray',
            bd=0,
            activebackground='gray'
        )
        self.step_button.pack(side=tk.LEFT, padx=5)

        # Create the pencil and eraser buttons
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

        # Create the nuke button to kill all cells
        self.nuke_button = tk.Button(
            self.toolbar,
            image=self.nuke_icon,
            command=self.clear_grid,
            bg='lightgray',
            bd=0,
            activebackground='gray'
        )
        self.nuke_button.pack(side=tk.LEFT, padx=5)

        # Create speed slider
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
        self.speed_slider.set(1)  # Default speed set to 1 (1 step every 0.25 seconds)
        self.speed_slider.pack(side=tk.RIGHT, padx=5)

    def draw_grid(self):
        """Draw grid lines on the canvas."""
        for i in range(self.rows):
            self.canvas.create_line(0, i * self.cell_size, self.canvas_size, i * self.cell_size, fill='black')
        for j in range(self.cols):
            self.canvas.create_line(j * self.cell_size, 0, j * self.cell_size, self.canvas_size, fill='black')

    def on_canvas_configure(self, event):
        """Update the scroll region of the canvas."""
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))

    def toggle(self):
        """Toggle the simulation between running and paused."""
        self.running = not self.running
        if self.running:
            self.toggle_button.config(image=self.pause_icon)
            self.run_simulation()
        else:
            self.toggle_button.config(image=self.play_icon)

    def step_simulation(self):
        """Step through one generation."""        
        self.update_grid()
        self.update_canvas()
    
    def run_simulation(self):
       if self.running:
            self.update_grid()  # Update the grid for the next generation
            self.update_canvas()  # Redraw the canvas
            self.master.after(250 // self.speed_slider.get(), self.run_simulation)  # Repeat the process

    def use_pencil_tool(self):
        """Enable the pencil tool."""        
        self.drawing = True

    def use_eraser_tool(self):
        """Enable the eraser tool."""        
        self.drawing = False

    def start_drawing(self, event):
        """Start drawing cells."""        
        self.last_x, self.last_y = event.x, event.y
        self.draw(event)

    def draw(self, event):
        """Draw cells or erase cells on the canvas."""        
        x, y = event.x // self.cell_size, event.y // self.cell_size

        if self.drawing:  # Drawing with pencil
            # Draw a line from the last position to the current position
            if self.last_x is not None and self.last_y is not None:
                self.draw_line(self.last_x, self.last_y, event.x, event.y)
            # Set the clicked cell to alive (1)
            if 0 <= x < self.cols and 0 <= y < self.rows:
                self.grid[y, x] = 1
                self.draw_cell(x, y)

        else:  # Erasing with eraser
            # Erase the cell (set it to 0)
            if 0 <= x < self.cols and 0 <= y < self.rows:
                self.grid[y, x] = 0
                self.clear_cell(x, y)

        # Update the last x and y
        self.last_x, self.last_y = event.x, event.y

    def stop_drawing(self, event):
        """Stop drawing or erasing."""        
        self.last_x, self.last_y = None, None

    def draw_line(self, x1, y1, x2, y2):
        """Draw a line from (x1, y1) to (x2, y2) using the grid."""        
        pass  # Logic for drawing a line between two points in the grid

    def draw_cell(self, x, y):
        """Draw a live cell at (x, y)."""        
        x1 = x * self.cell_size
        y1 = y * self.cell_size
        x2 = x1 + self.cell_size
        y2 = y1 + self.cell_size
        self.canvas.create_rectangle(x1, y1, x2, y2, fill="white", outline="black")

    def clear_cell(self, x, y):
        """Clear a dead cell at (x, y)."""        
        x1 = x * self.cell_size
        y1 = y * self.cell_size
        x2 = x1 + self.cell_size
        y2 = y1 + self.cell_size
        self.canvas.create_rectangle(x1, y1, x2, y2, fill="#2b2b2b", outline="black")

    def update_canvas(self):
        """Update the canvas by redrawing all cells."""
        self.canvas.delete("all")
        self.draw_grid()
        for y in range(self.rows):
            for x in range(self.cols):
                if self.grid[y, x] == 1:
                    self.draw_cell(x, y)

    def update_grid(self):
        """Update the grid for the next generation using the Game of Life rules."""
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
        """Count the live neighbors for a cell."""
        total = 0
        for i in range(-1, 2):
            for j in range(-1, 2):
                if not (i == 0 and j == 0):
                    total += self.grid[(row + i) % self.rows, (col + j) % self.cols]
        return total

    def clear_grid(self):
        """Clear the entire grid."""
        self.grid = np.zeros((self.rows, self.cols), dtype=int)
        self.update_canvas()

    def open_file(self):
        """Open a binary file and load the grid."""
        file_path = filedialog.askopenfilename(filetypes=[("Glide Life Projects", "*.glp")])
        if file_path:
            try:
                with open(file_path, 'rb') as file:
                    # Read the grid dimensions first
                    self.rows, self.cols = struct.unpack('II', file.read(8))
                    # Calculate the total number of cells
                    total_cells = self.rows * self.cols
                    # Read the flattened grid data
                    flat_grid = np.frombuffer(file.read(), dtype=int)
                    if flat_grid.size != total_cells:
                        raise ValueError("Corrupted file or grid size mismatch.")
                    # Reshape the grid
                    self.grid = flat_grid.reshape((self.rows, self.cols))
                    # Redraw the canvas
                    self.update_canvas()
            except Exception as e:
                messagebox.showerror("Error", f"Failed to open file: {str(e)}")
    
    def save_file(self):
        """Save the grid to a binary file."""
        file_path = filedialog.asksaveasfilename(defaultextension=".glp", filetypes=[("Glide Life Projects", "*.glp")])
        if file_path:
            with open(file_path, 'wb') as file:
                # Save grid dimensions first
                file.write(struct.pack('II', self.rows, self.cols))
                # Save the grid data as a flat array
                flat_grid = self.grid.flatten()
                file.write(flat_grid.tobytes())

# Main application
if __name__ == "__main__":
    root = tk.Tk()
    app = GameOfLife(root)
    root.mainloop()
    print("This software is made by Super Studios.")
