from tkinter import *
from tkinter import filedialog
from tkinter import messagebox
import pygame
import numpy as np
import os
import base64


# STL file loader class
class Loader:
    # Initialize class variables
    geometry = []
    normal = []
    name = []
    normal_face = []

    # Load ASCII STL File (no Binary STLs - based on project requirements)
    def load_stl(self, filename):
        self.geometry = []  # Clear previous geometry data
        self.name = []  # Clear previous STL model name
        self.normal = []  # Clear previous STL normal data
        fp = open(filename, 'r')  # Open and read selected file into memory

        # Loop over each line in the STL file
        for line in fp.readlines():
            parts = line.split()  # Split line into parts by spaces
            if len(parts) > 0:
                # Start of filename, store embedded filename
                if parts[0] == 'solid':
                    self.name = line[6:-1]
                    # Beginning of a new face - store normals and begin new triangle variable
                    if parts[0] == 'facet':
                        triangle = []
                        # Select face normal components
                        self.normal_face = (float(parts[2]), float(parts[3]), float(parts[4]), 1)
                    # Store all the vertex points in 'triangle'
                    if parts[0] == 'vertex':
                        triangle.append((float(parts[1]), float(parts[2]), float(parts[3]), 1))
                    # End of face - append new face to the model data
                    if parts[0] == 'endloop':
                        self.geometry.append([triangle[0], triangle[1], triangle[2]])
                        self.normal.append(self.normal_face)
        fp.close()
        # Convert lists to numpy arrays of the correct dimensions (Nx4 matrices)
        self.normal = np.asarray(self.normal).reshape((-1, 4))
        self.geometry = np.asarray(self.geometry).reshape((-1, 4))
        self.geometry = orient(self.geometry, embed_w, embed_h)  # Orient object geometry in screen space
        window.title("STL Viewer Application - " + self.name)  # Put filename in the GUI header


def file_select():
    # Function to select an STL file and store the path as "filename"
    window.filename = filedialog.askopenfilename(initialdir="C:\\", title="Select STL File",
                                                 filetypes=(("STL files", "*.STL"), ("All files", "*.*")))
    status_text = "Opened: " + window.filename  # Add file name/path to bottom status bar
    status.configure(text=status_text)
    file_select.stlobject = DrawObject()  # Create new stlobject class for the selected file
    DrawObject.initial_plot(file_select.stlobject, screen)  # Run initial object plot function for the class

def about_popup():
    # Info box about the software from the Help menu
    messagebox.showinfo('About STL Viewer',
                        'Created by Evan Chodora, 2018\n\n Designed to open and view ASCII STL files')

# ****** Initialize Main Window ******

window = Tk()
window.title('STL Viewer Application')  # Main window title

# Code to embed base64 version of the window icon into the title bar
cube = \
        "AAABAAEAICAAAAEAIACoEAAAFgAAACgAAAAgAAAAQAAAAAEAIAAAAAAAABAAANcNAADXDQAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA\
        AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAADwAAAFgAAADEAAAAxAAAAFgAAAAPAAAAAAAAAAAAAAAA\
        AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA\
        AAAAAAAAAAAAAAAADQAAAE4AAACwAAAA8gAAAP0AAAD+AAAA8AAAAK8AAABOAAAADQAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA\
        AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAADQAAAE8AAACxAAAA9AAAAP0A\
        AADSAAAAjAAAAOwAAAD/AAAA/wAAAPIAAACxAAAATwAAAA0AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA\
        AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAADQAAAE8AAACxAAAA9AAAAP0AAADTAAAAdgAAAB8AAAAdAAAA4wAAAP8AAAD/AAAA\
        /wAAAP8AAADyAAAAsQAAAE8AAAANAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAADQAA\
        AE8AAACxAAAA9AAAAP0AAADTAAAAdgAAACEAAAABAAAAAAAAABwAAADjAAAA/wAAAP8AAAD/AAAA/wAAAP8AAAD/AAAA8gAAALEA\
        AABPAAAADQAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAADQAAAE8AAACxAAAA9AAAAP0AAADTAAAAdgAAACEAAAAB\
        AAAAAAAAAAAAAAAAAAAAHAAAAOMAAAD/AAAA/wAAAP8AAAD/AAAA/wAAAP8AAAD/AAAA/wAAAPIAAACxAAAATwAAAA0AAAAAAAAA\
        AAAAAAAAAAAAAAAADQAAAE8AAACxAAAA9AAAAP0AAADTAAAAdgAAACEAAAABAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAcAAAA4wAA\
        AP8AAAD/AAAA/wAAAP8AAAD/AAAA/wAAAP8AAAD/AAAA/wAAAP8AAADyAAAAsQAAAE8AAAANAAAAAAAAAFYAAACwAAAA9AAAAP0A\
        AADTAAAAdgAAACEAAAABAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAABwAAADjAAAA/wAAAP8AAAD/AAAA/wAAAP8AAAD/\
        AAAA/wAAAP8AAAD/AAAA/wAAAP8AAAD/AAAA8gAAALAAAABWAAAA9QAAAP4AAADUAAAAdgAAACEAAAABAAAAAAAAAAAAAAAAAAAA\
        AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAHAAAAOMAAAD/AAAA/wAAAP8AAAD/AAAA/wAAAP8AAAD/AAAA/wAAAP8AAAD/AAAA/wAA\
        AP8AAAD/AAAA/wAAAPUAAAD/AAAA6QAAADQAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA\
        AAAcAAAA4wAAAP8AAAD/AAAA/wAAAP8AAAD/AAAA/wAAAP8AAAD/AAAA/wAAAP8AAAD/AAAA/wAAAP8AAAD/AAAA/wAAAP8AAADj\
        AAAAHAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAABwAAADjAAAA/wAAAP8AAAD/AAAA\
        /wAAAP8AAAD/AAAA/wAAAP8AAAD/AAAA/wAAAP8AAAD/AAAA/wAAAP8AAAD/AAAA/wAAAOMAAAAcAAAAAAAAAAAAAAAAAAAAAAAA\
        AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAHAAAAOMAAAD/AAAA/wAAAP8AAAD/AAAA/wAAAP8AAAD/AAAA/wAAAP8A\
        AAD/AAAA/wAAAP8AAAD/AAAA/wAAAP8AAAD/AAAA4wAAABwAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA\
        AAAAAAAAAAAAAAAcAAAA4wAAAP8AAAD/AAAA/wAAAP8AAAD/AAAA/wAAAP8AAAD/AAAA/wAAAP8AAAD/AAAA/wAAAP8AAAD/AAAA\
        /wAAAP8AAADjAAAAHAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAABwAAADjAAAA/wAA\
        AP8AAAD/AAAA/wAAAP8AAAD/AAAA/wAAAP8AAAD/AAAA/wAAAP8AAAD/AAAA/wAAAP8AAAD/AAAA/wAAAOMAAAAcAAAAAAAAAAAA\
        AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAHAAAAOMAAAD/AAAA/wAAAP8AAAD/AAAA/wAAAP8AAAD/\
        AAAA/wAAAP8AAAD/AAAA/wAAAP8AAAD/AAAA/wAAAP8AAAD/AAAA4wAAABwAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA\
        AAAAAAAAAAAAAAAAAAAAAAAAAAAcAAAA4wAAAP8AAAD/AAAA/wAAAP8AAAD/AAAA/wAAAP8AAAD/AAAA/wAAAP8AAAD/AAAA/wAA\
        AP8AAAD/AAAA/wAAAP8AAADjAAAAHAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAABwA\
        AADjAAAA/wAAAP8AAAD/AAAA/wAAAP8AAAD/AAAA/wAAAP8AAAD/AAAA/wAAAP8AAAD/AAAA/wAAAP8AAAD/AAAA/wAAAOMAAAAc\
        AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAHAAAAOMAAAD/AAAA/wAAAP8AAAD/AAAA\
        /wAAAP8AAAD/AAAA/wAAAP8AAAD/AAAA/wAAAP8AAAD/AAAA/wAAAP8AAAD/AAAA4wAAABwAAAAAAAAAAAAAAAAAAAAAAAAAAAAA\
        AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAcAAAA4wAAAP8AAAD/AAAA/wAAAP8AAAD/AAAA/wAAAP8AAAD/AAAA/wAAAP8A\
        AAD/AAAA/wAAAP8AAAD/AAAA/wAAAP8AAADjAAAAHAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA\
        AAAAAAAAABwAAADjAAAA/wAAAP8AAAD/AAAA/wAAAP8AAAD/AAAA/wAAAP8AAAD/AAAA/wAAAP8AAAD/AAAA/wAAAP8AAAD/AAAA\
        /wAAAOMAAAAcAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAMAAAAWAAAAWQAAAO4AAAD/AAAA/wAA\
        AP8AAAD/AAAA/wAAAP8AAAD/AAAA/wAAAP8AAAD/AAAA/wAAAP8AAAD/AAAA/wAAAP8AAAD/AAAA4wAAABwAAAAAAAAAAAAAAAAA\
        AAAAAAAAAAAAAAAAAAAAAAAAAgAAABMAAABEAAAAiQAAAM0AAAD1AAAA/wAAAP8AAAD/AAAA/wAAAP8AAAD/AAAA/wAAAP8AAAD/\
        AAAA/wAAAP8AAAD/AAAA/wAAAP8AAAD/AAAA/wAAAP8AAADjAAAAHAAAAAAAAAAAAAAAAAAAAAAAAAABAAAAEQAAAD8AAACDAAAA\
        xwAAAPIAAAD/AAAA9QAAAM4AAACQAAAAlAAAANYAAAD5AAAA/wAAAP8AAAD/AAAA/wAAAP8AAAD/AAAA/wAAAP8AAAD/AAAA/wAA\
        AP8AAAD/AAAA/wAAAOMAAAAcAAAAAAAAAAEAAAAPAAAAOQAAAH0AAADCAAAA8AAAAP4AAAD1AAAAzwAAAI4AAABLAAAAGAAAAAMA\
        AAAEAAAAHwAAAF4AAACqAAAA5QAAAPwAAAD/AAAA/wAAAP8AAAD/AAAA/wAAAP8AAAD/AAAA/wAAAP8AAAD/AAAA5AAAACgAAAAy\
        AAAAdgAAALsAAADuAAAA/gAAAPUAAADPAAAAjgAAAEsAAAAYAAAAAwAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAkAAAAwAAAA\
        dgAAAMAAAADvAAAA/gAAAP8AAAD/AAAA/wAAAP8AAAD/AAAA/wAAAP8AAAD0AAAAwQAAAOgAAAD9AAAA9AAAAM4AAACNAAAASgAA\
        ABcAAAADAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAABAAAAEQAAAEQAAACOAAAA0wAAAPYA\
        AAD/AAAA/wAAAP8AAAD/AAAA/wAAAP8AAAD/AAAA+QAAALEAAABVAAAAFQAAAAEAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA\
        AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAEAAAAgAAAAbwAAANQAAAD/AAAA/wAAAP8AAADtAAAA\
        +wAAAP8AAAD+AAAA4wAAALAAAAB8AAAASQAAAB4AAAAJAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA\
        AAAAAAAAAAAABQAAABQAAAA2AAAAZwAAAJgAAADJAAAA8wAAAP8AAAD7AAAA7QAAADgAAABmAAAAmQAAAMoAAADtAAAA/AAAAP8A\
        AAD1AAAA2wAAAKkAAAB0AAAAQAAAABgAAAAGAAAAAAAAAAAAAAAAAAAAAAAAAAQAAAAUAAAANQAAAGYAAACZAAAAzAAAAO4AAAD9\
        AAAA/AAAAO4AAADLAAAAmQAAAGYAAAA4AAAAAAAAAAAAAAAEAAAAFAAAADUAAABmAAAAmQAAAMsAAADtAAAA/AAAAP4AAADyAAAA\
        0wAAAJ8AAABqAAAANwAAADYAAABmAAAAmQAAAMwAAADuAAAA/QAAAPwAAADuAAAAzAAAAJkAAABmAAAANQAAABQAAAAEAAAAAAAA\
        AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAEAAAAFAAAADUAAABmAAAAmAAAAMoAAADsAAAA+wAAAPwAAADtAAAA7QAAAPwA\
        AAD8AAAA7AAAAMoAAACYAAAAZgAAADUAAAAUAAAABAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA\
        AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAFAAAAFwAAADwAAABzAAAArAAAAOMAAADjAAAArAAAAHMAAAA8AAAAFwAAAAUAAAAAAAAA\
        AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA//gf///gB///gAH//gAAf/gCAB/gDgAHgD4AAQD+AAAD/gAAH/4AAB/+\
        AAAf/gAAH/4AAB/+AAAf/gAAH/4AAB/+AAAf/gAAH/4AAB/+AAAf+AAAH8AAAB4AAAAQAAAAAAPwAAAf/AAA//+AAD/8AAADwADA\
        AAAD/AAAP//AA/8="

icondata = base64.b64decode(cube)  # Decode base64 image
tempfile = "icon.ico"  # Create temporary file
iconfile = open(tempfile, "wb")  # Open temporary file
iconfile.write(icondata)  # Write icon data
iconfile.close()
window.wm_iconbitmap(tempfile)  # Set window icon to the icon image
os.remove(tempfile)

window.geometry("1200x800")  # Main overall window size
window.resizable(0, 0)  # Scaling disallowed in X and Y

# ****** Embed PyGame Window (Pixel Map Display) ******

embed_w = 900  # Width of object display screen
embed_h = 700  # Height of object display screen
embed = Frame(window, width=embed_w, height=embed_h)  # Embed in the GUI window
embed.place(x=50, y=40)  # Location of placement
# Set appropriate environment variables for embedding the PyGame pixel display window in the GUI
os.environ['SDL_WINDOWID'] = str(embed.winfo_id())
os.environ['SDL_VIDEODRIVER'] = 'windib'
screen = pygame.display.set_mode((embed_w, embed_h))  # Create screen with specified width and height
# Set embed screen to white and refresh the screen object
screen.fill((255, 255, 255))
pygame.display.init()
pygame.display.flip()

# ****** Define Default Perspective Settings and View Type ******

persp = StringVar()
persp.set('iso')
view = StringVar()
view.set('hide')
phi = DoubleVar()
phi.set(45)
theta = DoubleVar()
theta.set(35)
fz = DoubleVar()
fz.set(0.375)

# ****** Toolbar ******

# Create main menu bar
menu = Menu(window, tearoff=False)
window.config(menu=menu)

# Create "File" submenu
subMenu = Menu(menu, tearoff=False)
menu.add_cascade(label="File", menu=subMenu)
subMenu.add_command(label="Open File", command=file_select)
subMenu.add_command(label="Exit", command=window.destroy)

# Create "Edit View" submenu
subMenu = Menu(menu, tearoff=False)
menu.add_cascade(label="Edit View", menu=subMenu)
perspMenu = Menu(subMenu, tearoff=False)
subMenu.add_cascade(label="Change Perspective", menu=perspMenu)
perspMenu.add_radiobutton(label='Isometric', variable=persp, value='iso')  # Isometric projection
perspMenu.add_radiobutton(label='Dimetric', variable=persp, value='di')  # Dimetric projection
perspMenu.add_radiobutton(label='Trimetric', variable=persp, value='tri')  # Trimetric projection
viewMenu = Menu(subMenu, tearoff=False)
subMenu.add_cascade(label="View Type", menu=viewMenu)
viewMenu.add_radiobutton(label='Wireframe', variable=view, value='wire')  # Full wireframe
viewMenu.add_radiobutton(label='Hide Faces', variable=view, value='hide')  # Hide non-visible faces
viewMenu.add_radiobutton(label='Partial Hidden', variable=view, value='grey')  # Grey hidden lines
subMenu.add_command(label="Recenter Object", command=lambda: DrawObject.initial_plot(file_select.stlobject, screen))
subMenu.add_command(label="Perspective Settings", command=save_click)

# Create "Orthographic" submenu
subMenu = Menu(menu, tearoff=False)
menu.add_cascade(label="Orthographic", menu=subMenu)
subMenu.add_command(label="Top", command=lambda: DrawObject.plot_transform(file_select.stlobject, screen,
                                                                           'ortho', 'top'))
subMenu.add_command(label="Bottom", command=lambda: DrawObject.plot_transform(file_select.stlobject, screen,
                                                                              'ortho', 'bottom'))
subMenu.add_command(label="Left", command=lambda: DrawObject.plot_transform(file_select.stlobject, screen,
                                                                            'ortho', 'left'))
subMenu.add_command(label="Right", command=lambda: DrawObject.plot_transform(file_select.stlobject, screen,
                                                                             'ortho', 'right'))
subMenu.add_command(label="Front", command=lambda: DrawObject.plot_transform(file_select.stlobject, screen,
                                                                             'ortho', 'front'))
subMenu.add_command(label="Back", command=lambda: DrawObject.plot_transform(file_select.stlobject, screen,
                                                                            'ortho', 'back'))

# Create "Help" submenu
subMenu = Menu(menu, tearoff=False)
menu.add_cascade(label="Help", menu=subMenu)
subMenu.add_command(label="About", command=about_popup)

# ****** Control Panel ******

# Control text labels
rotate = Label(window, text="Rotate", font=("Helvetica", 16))
rotate.place(x=1075, rely=0.15, anchor="c")
zoom = Label(window, text="Zoom", font=("Helvetica", 16))
zoom.place(x=1075, rely=0.45, anchor="c")
pan = Label(window, text="Pan", font=("Helvetica", 16))
pan.place(x=1075, rely=0.65, anchor="c")

# Rotation buttons layout
rot_l = Button(window, text="<-", width=5, command=lambda: DrawObject.plot_transform(file_select.stlobject, screen,
                                                                                     'rotation', [2, -15]))
rot_l.place(x=1025, rely=.25, anchor="c")
rot_r = Button(window, text="->", width=5, command=lambda: DrawObject.plot_transform(file_select.stlobject, screen,
                                                                                     'rotation', [2, 15]))
rot_r.place(x=1125, rely=.25, anchor="c")
rot_u = Button(window, text="/\\", width=5, command=lambda: DrawObject.plot_transform(file_select.stlobject, screen,
                                                                                      'rotation', [1, -15]))
rot_u.place(x=1075, rely=.2, anchor="c")
rot_d = Button(window, text="\\/", width=5, command=lambda: DrawObject.plot_transform(file_select.stlobject, screen,
                                                                                      'rotation', [1, 15]))
rot_d.place(x=1075, rely=.3, anchor="c")

# Zoom buttons layout
zoom_in = Button(window, text="+", width=5, command=lambda: DrawObject.plot_transform(file_select.stlobject, screen,
                                                                                      'zoom', [0.8]))
zoom_in.place(x=1025, rely=.5, anchor="c")
zoom_out = Button(window, text="-", width=5, command=lambda: DrawObject.plot_transform(file_select.stlobject, screen,
                                                                                       'zoom', [1.25]))
zoom_out.place(x=1125, rely=.5, anchor="c")

# Panning buttons layout
pan_l = Button(window, text="<-", width=5, command=lambda: DrawObject.plot_transform(file_select.stlobject, screen,
                                                                                     'translate', [-20, 0, 0]))
pan_l.place(x=1025, rely=.75, anchor="c")
pan_r = Button(window, text="->", width=5, command=lambda: DrawObject.plot_transform(file_select.stlobject, screen,
                                                                                     'translate', [20, 0, 0]))
pan_r.place(x=1125, rely=.75, anchor="c")
pan_u = Button(window, text="/\\", width=5, command=lambda: DrawObject.plot_transform(file_select.stlobject, screen,
                                                                                      'translate', [0, -20, 0]))
pan_u.place(x=1075, rely=.7, anchor="c")
pan_d = Button(window, text="\\/", width=5, command=lambda: DrawObject.plot_transform(file_select.stlobject, screen,
                                                                                      'translate', [0, 20, 0]))
pan_d.place(x=1075, rely=.8, anchor="c")

# ****** Keyboard Control Bindings ******

window.bind("<Left>", lambda event: DrawObject.plot_transform(file_select.stlobject, screen, 'rotation', [2, -15]))
window.bind("<Right>", lambda event: DrawObject.plot_transform(file_select.stlobject, screen, 'rotation', [2, 15]))
window.bind("<Up>", lambda event: DrawObject.plot_transform(file_select.stlobject, screen, 'rotation', [1, -15]))
window.bind("<Down>", lambda event: DrawObject.plot_transform(file_select.stlobject, screen, 'rotation', [1, 15]))
window.bind("<a>", lambda event: DrawObject.plot_transform(file_select.stlobject, screen, 'translate', [-20, 0, 0]))
window.bind("<d>", lambda event: DrawObject.plot_transform(file_select.stlobject, screen, 'translate', [20, 0, 0]))
window.bind("<w>", lambda event: DrawObject.plot_transform(file_select.stlobject, screen, 'translate', [0, -20, 0]))
window.bind("<s>", lambda event: DrawObject.plot_transform(file_select.stlobject, screen, 'translate', [0, 20, 0]))
window.bind("<k>", lambda event: DrawObject.plot_transform(file_select.stlobject, screen, 'zoom', [0.8]))
window.bind("<l>", lambda event: DrawObject.plot_transform(file_select.stlobject, screen, 'zoom', [1.25]))

# ****** Status Bar ******

status = Label(window, text="Waiting...", bd=1, relief=SUNKEN, anchor=W)
status.pack(side=BOTTOM, fill=X)

# ****** Run Main GUI Loop ******

window.mainloop()  # Main loop to run the GUI, waits for button input
