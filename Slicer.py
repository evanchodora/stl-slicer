from tkinter import *
from tkinter import filedialog
from tkinter import messagebox
import pygame
import numpy as np
import os
import base64
import gtransform
import orient
import slice
import path
from drawlines import draw_lines


# Class to draw an STL object from an ASCII STL file
class DrawObject:
    pxarray = []  # Initialize the pixel array variable to empty for the class

    def __init__(self):
        # Initiate new Loader class and run load_stl with the selected file
        self.model = Loader()
        self.model.load_stl(window.filename)

    # Function to plot the initial object after loading
    def plot(self, loc):

        self.model.geometry = orient.to_origin(self.model.geometry)
        self.model.geometry = orient.fit_bed(self.model.geometry, xdim.get(), ydim.get(), zdim.get())
        # Apply selected perspective with appropriate settings of fz, phi, and theta
        plot_geometry, camera = gtransform.perspective(self.model.geometry)
        # Draw lines between points and clip to viewing window based on window height and width
        plot_geometry = draw_lines(plot_geometry, self.model.normal, camera, view.get())

        # Clear pixel array to white and then change each pixel color based on the XY pixel map
        self.pxarray = pygame.PixelArray(loc)
        self.pxarray[:][:] = (255, 255, 255)
        for point in range(0, plot_geometry.shape[0]):
            x = int(embed_w/2 + plot_geometry[point, 0])  # X coordinate (0,0 of screen is top left)
            y = int(embed_h/2 + plot_geometry[point, 1])  # Y coordinate (0,0 of screen is top left)
            # Plot all front facing lines and back facing when wireplot is selected
            if plot_geometry[point, 2] == 1 or view.get() == 'wire':
                self.pxarray[x][y] = (0, 0, 0)  # Color = black
            # Plot grey lines only if grey lines are selected and the line is not already plotted black
            elif plot_geometry[point, 2] == 0 and view.get() == 'grey' and self.pxarray[x][y] != 0:
                self.pxarray[x][y] = (210, 210, 210)  # Color = grey
        # Plot pixel array to screen and refresh window/GUI
        pygame.surfarray.blit_array(loc, self.pxarray)
        pygame.display.flip()
        window.update()

    # Function to apply a specified transformation to the object
    def plot_transform(self, loc, transtype, data):

        # Transform geometry based on the selected transformation
        self.model.geometry, self.model.normal = gtransform.transform(self.model.geometry, self.model.normal, transtype,
                                                                      data)
        self.plot(loc)  # Rescale within print bed and plot the geometry for the new orientation

    # Function to run the slicer algorithm
    def slice_geometry(self):

        # Calculate slice thickness/number of slices parameters
        h = ydim.get()
        step = slice_size.get()
        num_steps = int(h/step)

        # Try to delete a path file if it exists
        try:
            os.remove('outputs/path.csv')
        except OSError:
            pass

        # Loop over the number of slices through the print area based on the slice thickness selected
        for level in range(num_steps+2):
            offset = 0.025  # Negligible offset to handle rounding error with first and last slice (<0.001 in)
            if level == 0:
                z = round(level * step + offset, 2)
            elif level == num_steps + 1:
                z = round(level * step - offset, 2)
            else:
                z = round(level * step + offset, 2)

            # Rotate the object around the X-axis by 180deg to align with print bed coordinate system
            geometry, normals = gtransform.rotation(self.model.geometry, self.model.normal, 1, 180)
            # Compute the clipped point pairs at the current slice z coordinate
            point_pairs = slice.compute_points_on_z(geometry, z, xdim.get(), ydim.get(), zdim.get())
            # Output the slices to svg files for confirmation (optional)
            path.svgcreate(point_pairs, z, xdim.get())
            # Run the contour building algorithm to sort the point pairs into continous contour sets
            contour = slice.build_contours(point_pairs)
            # Create printer head path CSV file
            path.headpath(contour, z)


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
        triangle = []  # Initialize empty triangle set
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
        window.title("STL Slicer Application - " + self.name)  # Put filename in the GUI header


def file_select():
    # Function to select an STL file and store the path as "filename"
    window.filename = filedialog.askopenfilename(initialdir="C:\\", title="Select STL File",
                                                 filetypes=(("STL files", "*.STL"), ("All files", "*.*")))
    # Check whether or not a file was selected or not
    if window.filename:
        status_text = "Opened: " + window.filename  # Add file name/path to bottom status bar
        status.configure(text=status_text)
        file_select.stlobject = DrawObject()  # Create new stlobject class for the selected file
        DrawObject.plot(file_select.stlobject, screen)  # Run initial object plot function for the class


# Class to create a perspective settings popup dialog box for user input
class SettingsDialog:
    def __init__(self, parent):
        top = self.top = Toplevel(parent)  # Use Tkinter top for a separate popup GUI
        top.geometry("240x200")  # Window dimensions
        top.resizable(0, 0)  # Un-resizable
        top.title('Settings')  # Window title

        # Code to assign an icon to the settings popup box using base64 stored image
        icon = \
            "AAABAAEAICAAAAEAIACoEAAAFgAAACgAAAAgAAAAQAAAAAEAIAAAAAAAABAAANcNAADXDQAAAAAAAAAA\
            AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAZwAA\
            AOkAAAD5AAAA+QAAAOUAAABVAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA\
            AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA\
            AAcAAACjAAAA/wAAAP8AAAD/AAAA/wAAAJAAAAABAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA\
            AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA\
            AAAAAAAAAAAAHQAAANAAAAD/AAAA/wAAAP8AAAD/AAAAwwAAABYAAAAAAAAAAAAAAAAAAAAAAAAAAQAA\
            AAQAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAADIAAACGAAAAQgAA\
            AAMAAAAAAAAAAAAAAAwAAACEAAAA+wAAAP8AAAD/AAAA/wAAAP8AAAD5AAAAgAAAAA0AAAAAAAAAAAAA\
            AAoAAABcAAAAlgAAADAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAzAAAAyQAA\
            AP8AAADjAAAAiwAAAFgAAABgAAAApwAAAPUAAAD/AAAA/wAAAP8AAAD/AAAA/wAAAP8AAAD1AAAArgAA\
            AHAAAABvAAAApwAAAPEAAAD/AAAAyAAAADMAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAMAAA\
            AMgAAAD/AAAA/wAAAP8AAAD+AAAA9wAAAPkAAAD/AAAA/wAAAP8AAAD/AAAA/wAAAP8AAAD/AAAA/wAA\
            AP8AAAD/AAAA/QAAAP0AAAD/AAAA/wAAAP8AAAD/AAAAygAAADIAAAAAAAAAAAAAAAAAAAAAAAAAAAAA\
            AAIAAACQAAAA/wAAAP8AAAD/AAAA/wAAAP8AAAD/AAAA/wAAAP8AAAD/AAAA/wAAAP8AAAD/AAAA/wAA\
            AP8AAAD/AAAA/wAAAP8AAAD/AAAA/wAAAP8AAAD/AAAA/wAAAP8AAAD/AAAAhQAAAAAAAAAAAAAAAAAA\
            AAAAAAAAAAAAAAAAAFQAAADuAAAA/wAAAP8AAAD/AAAA/wAAAP8AAAD/AAAA/wAAAP8AAAD/AAAA/wAA\
            AP8AAAD/AAAA/wAAAP8AAAD/AAAA/wAAAP8AAAD/AAAA/wAAAP8AAAD/AAAA/wAAAOAAAAA/AAAAAAAA\
            AAAAAAAAAAAAAAAAAAAAAAAAAAAABgAAAJwAAAD/AAAA/wAAAP8AAAD/AAAA/wAAAP8AAAD/AAAA/wAA\
            AP8AAAD/AAAA/wAAAP8AAAD/AAAA/wAAAP8AAAD/AAAA/wAAAP8AAAD/AAAA/wAAAP8AAAD/AAAAhgAA\
            AAEAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAZgAAAPwAAAD/AAAA/wAAAP8AAAD/AAAA/wAA\
            AP8AAAD/AAAA/wAAAP8AAAD/AAAA/wAAAP8AAAD/AAAA/wAAAP8AAAD/AAAA/wAAAP8AAAD/AAAA/wAA\
            APUAAABTAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAABsAAAA/QAAAP8AAAD/AAAA/wAA\
            AP8AAAD/AAAA/wAAAP8AAAD2AAAA1gAAAK8AAACtAAAA0wAAAPUAAAD/AAAA/wAAAP8AAAD/AAAA/wAA\
            AP8AAAD/AAAA+AAAAFwAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAADgAAAK0AAAD/AAAA/wAA\
            AP8AAAD/AAAA/wAAAP8AAAD/AAAA2AAAAGUAAAAaAAAACgAAAAoAAAAZAAAAXwAAANQAAAD/AAAA/wAA\
            AP8AAAD/AAAA/wAAAP8AAAD/AAAApgAAAAwAAAAAAAAAAAAAAAAAAAAAAAAAAgAAABYAAACBAAAA9gAA\
            AP8AAAD/AAAA/wAAAP8AAAD/AAAA/wAAANkAAAA6AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAANAAA\
            ANQAAAD/AAAA/wAAAP8AAAD/AAAA/wAAAP8AAAD1AAAAhAAAABsAAAAGAAAAAAAAAFQAAACUAAAAxwAA\
            APgAAAD/AAAA/wAAAP8AAAD/AAAA/wAAAP8AAAD4AAAAagAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA\
            AAAAAAAAAAAAYAAAAPYAAAD/AAAA/wAAAP8AAAD/AAAA/wAAAP8AAAD5AAAA0AAAAKQAAABnAAAA4AAA\
            AP8AAAD/AAAA/wAAAP8AAAD/AAAA/wAAAP8AAAD/AAAA/wAAAN0AAAAfAAAAAAAAAAAAAAAAAAAAAAAA\
            AAAAAAAAAAAAAAAAAAAAAAAaAAAA1gAAAP8AAAD/AAAA/wAAAP8AAAD/AAAA/wAAAP8AAAD/AAAA/wAA\
            AOIAAADpAAAA/wAAAP8AAAD/AAAA/wAAAP8AAAD/AAAA/wAAAP8AAAD/AAAAuQAAAA4AAAAAAAAAAAAA\
            AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAsAAACwAAAA/wAAAP8AAAD/AAAA/wAAAP8AAAD/AAAA/wAA\
            AP8AAAD/AAAA6AAAAOgAAAD/AAAA/wAAAP8AAAD/AAAA/wAAAP8AAAD/AAAA/wAAAP8AAAC8AAAADwAA\
            AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAADAAAALIAAAD/AAAA/wAAAP8AAAD/AAAA/wAA\
            AP8AAAD/AAAA/wAAAP8AAADpAAAA4gAAAP8AAAD/AAAA/wAAAP8AAAD/AAAA/wAAAP8AAAD/AAAA/wAA\
            AN8AAAAiAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAcAAAA2AAAAP8AAAD/AAAA/wAA\
            AP8AAAD/AAAA/wAAAP8AAAD/AAAA/wAAAOAAAABoAAAAqAAAANUAAAD6AAAA/wAAAP8AAAD/AAAA/wAA\
            AP8AAAD/AAAA+gAAAHEAAAABAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAGgAAAD4AAAA/wAA\
            AP8AAAD/AAAA/wAAAP8AAAD/AAAA+AAAAMkAAACVAAAAVQAAAAEAAAAIAAAAIAAAAIkAAAD2AAAA/wAA\
            AP8AAAD/AAAA/wAAAP8AAAD/AAAA3wAAAEQAAAABAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA+AAAA2gAA\
            AP8AAAD/AAAA/wAAAP8AAAD/AAAA/wAAAPYAAACCAAAAFwAAAAMAAAAAAAAAAAAAAAAAAAAAAAAADQAA\
            AKcAAAD/AAAA/wAAAP8AAAD/AAAA/wAAAP8AAAD/AAAA4AAAAHEAAAAhAAAADwAAAA8AAAAgAAAAbAAA\
            ANwAAAD/AAAA/wAAAP8AAAD/AAAA/wAAAP8AAAD/AAAArgAAAA4AAAAAAAAAAAAAAAAAAAAAAAAAAAAA\
            AAAAAAAAAAAAXQAAAPgAAAD/AAAA/wAAAP8AAAD/AAAA/wAAAP8AAAD/AAAA+AAAAOAAAAC+AAAAvAAA\
            AN4AAAD4AAAA/wAAAP8AAAD/AAAA/wAAAP8AAAD/AAAA/wAAAP0AAABsAAAAAAAAAAAAAAAAAAAAAAAA\
            AAAAAAAAAAAAAAAAAAAAAABTAAAA9QAAAP8AAAD/AAAA/wAAAP8AAAD/AAAA/wAAAP8AAAD/AAAA/wAA\
            AP8AAAD/AAAA/wAAAP8AAAD/AAAA/wAAAP8AAAD/AAAA/wAAAP8AAAD/AAAA/AAAAGYAAAAAAAAAAAAA\
            AAAAAAAAAAAAAAAAAAAAAAAAAAAAAQAAAIYAAAD/AAAA/wAAAP8AAAD/AAAA/wAAAP8AAAD/AAAA/wAA\
            AP8AAAD/AAAA/wAAAP8AAAD/AAAA/wAAAP8AAAD/AAAA/wAAAP8AAAD/AAAA/wAAAP8AAAD/AAAAnAAA\
            AAYAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA/AAAA4AAAAP8AAAD/AAAA/wAAAP8AAAD/AAAA/wAA\
            AP8AAAD/AAAA/wAAAP8AAAD/AAAA/wAAAP8AAAD/AAAA/wAAAP8AAAD/AAAA/wAAAP8AAAD/AAAA/wAA\
            AP8AAADuAAAAVAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAIUAAAD/AAAA/wAAAP8AAAD/AAAA/wAA\
            AP8AAAD/AAAA/wAAAP8AAAD/AAAA/wAAAP8AAAD/AAAA/wAAAP8AAAD/AAAA/wAAAP8AAAD/AAAA/wAA\
            AP8AAAD/AAAA/wAAAP8AAACQAAAAAgAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAMgAAAMoAAAD/AAAA/wAA\
            AP8AAAD/AAAA/gAAAP0AAAD/AAAA/wAAAP8AAAD/AAAA/wAAAP8AAAD/AAAA/wAAAP8AAAD/AAAA+QAA\
            APcAAAD+AAAA/wAAAP8AAAD/AAAAyAAAADAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAMwAA\
            AMgAAAD/AAAA8QAAAKcAAABvAAAAbwAAAK4AAAD1AAAA/wAAAP8AAAD/AAAA/wAAAP8AAAD/AAAA9AAA\
            AKYAAABgAAAAWAAAAIsAAADjAAAA/wAAAMkAAAAzAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA\
            AAAAAAAAAAAAMAAAAJYAAABcAAAACgAAAAAAAAAAAAAADQAAAIAAAAD5AAAA/wAAAP8AAAD/AAAA/wAA\
            APoAAACDAAAADAAAAAAAAAAAAAAAAwAAAEAAAACFAAAAMgAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA\
            AAAAAAAAAAAAAAAAAAAAAAAAAAAABAAAAAEAAAAAAAAAAAAAAAAAAAAAAAAAFgAAAMMAAAD/AAAA/wAA\
            AP8AAAD/AAAAzwAAABwAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA\
            AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAABAAAAkAAA\
            AP8AAAD/AAAA/wAAAP8AAACjAAAABwAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA\
            AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA\
            AAAAAABVAAAA4QAAAOoAAADoAAAA5AAAAGcAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA\
            AAAAAAAAAAAAAAAAAAAAAAAA//gf///wD///8A8/+GAGH/AAAA/gAAAHwAAAB+AAAAfgAAAH8AAAD/AA\
            AA/gAAAHgAfgAQAP8AAAD/AAAA/wAAAP8AAAD/AAAAfwAAAD4AHgAAAH8AAAD/AAAA/gAAAH4AAAB+AA\
            AAPgAAAH8AAAD/hgBh/88A////AP///4H/8="

        icodata = base64.b64decode(icon)  # Decode base64 image
        temfile = "icon.ico"  # Create temporary file
        icofile = open(temfile, "wb")  # Open temporary file
        icofile.write(icodata)  # Write icon data
        icofile.close()
        top.wm_iconbitmap(temfile)  # Set window icon to the icon image
        os.remove(temfile)

        self.DiLabel = Label(top, text='Slicer Settings').place(x=50, rely=.05, anchor="c")
        self.fzLabel = Label(top, text='Fz').place(x=45, rely=.2, anchor="c")
        self.phiLabel = Label(top, text='Phi').place(x=45, rely=.5, anchor="c")
        self.thetaLabel = Label(top, text='Theta').place(x=45, rely=.65, anchor="c")
        self.TriLabel = Label(top, text='Trimetric Settings').place(x=50, rely=.35, anchor="c")
        self.fzBox = Entry(top)  # Fz entry box
        self.fzBox.place(x=140, rely=.2, anchor="c")
        self.fzBox.insert(0, fz.get())  # Prefill with Fz variable value
        self.phiBox = Entry(top)  # Phi entry box
        self.phiBox.place(x=140, rely=.5, anchor="c")
        self.phiBox.insert(0, phi.get())  # Prefill with Phi variable value
        self.thetaBox = Entry(top)  # Theta entry box
        self.thetaBox.place(x=140, rely=.65, anchor="c")
        self.thetaBox.insert(0, theta.get())  # Prefill with Theta variable value
        # Save button, runs command to store/send variables back to the main window space
        self.mySubmitButton = Button(top, text='Save', command=self.send).place(relx=.5, rely=.85, anchor="c")


def save_click():
    SettingsDialog(window)  # Create a new instance of the popup window class


def about_popup():
    # Info box about the software from the Help menu
    messagebox.showinfo('About STL Slicer',
                        'Created by Evan Chodora, 2018\n\n Designed to open and view ASCII STL files and perform'
                        ' geometry slicing')


# ****** Initialize Main Window ******

window = Tk()
window.title('STL Slicer Application')  # Main window title
window.geometry("1100x720")  # Main overall window size
window.resizable(0, 0)  # Scaling disallowed in X and Y

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

# ****** Embed PyGame Window (Pixel Map Display) ******

embed_w = 800  # Width of object display screen
embed_h = 600  # Height of object display screen
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

# Code to load a base64 version of the coordinate axes to display on the GUI for the print bed coordinate system
coords = \
        "iVBORw0KGgoAAAANSUhEUgAAAHgAAABiCAYAAACbKRcvAAAABHNCS\
        VQICAgIfAhkiAAAAAlwSFlzAAAHsgAAB7IBq3xA6wAAABl0RVh0U2\
        9mdHdhcmUAd3d3Lmlua3NjYXBlLm9yZ5vuPBoAAAWPSURBVHic7Z1\
        tiBVVGMd/u+2au72Z+VbWmlSGBYaU9EKFxRa9aNSHhAo2MuiTskWQ\
        QYV+s4JM6UtCEYh9sReWVmEhCYteyKwoFAwyIZOKrTZ1fSnT24dnh\
        jtzZu7duXdn7rn73OcHw7Jz3p6d/5wzzzzn7BwwDMMwDMMHbb4NKJ\
        ApwPYay2wDVhdgizc6fBtQIB3AtTWW2VOEIT5p922AUSyae/ARYFm\
        V9OeAa5xzO4szx2gkfUDJOTZ7tcjIjRuAE8TF/Rbo9mmUkQ+zgF+I\
        i/sHMNenUUY+dAKfEBf3JLDYo01Gjmwk+dxd4dUiIzceJSnuJq8WG\
        blxI0mn6mugy6dRRj6kOVW/ARf7NMrIhzSn6l/gVp9GNRrNkw0rgN\
        ecc8PAd2OUewAYLcQiD2gOVZ6dcm460DtGOVXXxCYblKPqbnUYAPb\
        VUe5o3oYYRmGc4duABtODzBqVgN2ebWkIrfYMPhdYAszzbUijaDWB\
        Ww4TWDkmsHJMYOWYwMoxgZVjAivHBFaOCawcE1g5JrByTGDlmMDKM\
        YGVYwIrxwRWjgmsHBNYOSawckxg5ZjAyjGBlWMCK8cEVo4JrBwTWD\
        kmsHJMYOWYwMoxgZVjAivHBFaOCawcE1g5JrByTGDltJrAZwY/p3q\
        1wiiEpcB+5OuzJ4ENwHleLTJyYSHwMfJtrL+AdcBXlD8t/DitN5Kp\
        4AKkl/4HnEK+8D4jSGsDHgR+pvyB8Fs82GjUQSfQD/yNiPcRsKBC3\
        rOANcDxIO8gcGnhFhp104t8orCE9M6+jOUuB7YE5Y4CL5L+OWLDE/\
        OArYhAo0ivnFxHPbcD3wf1HEBuEM0fTW96zkd62z/AaaQX9oyzzg7\
        gCeTr8CVgB8k9Do2CaUd61++ICDuBm3JuYyqVnTSjQG5D9l0oAQcp\
        fhidDwwF7Y0Aq4BJBbbXslyC9KIScAwZms9pYPtLgZ+C9n8A7mlg2\
        6pJe5XxtZlkF9KDDwe2fAhc5cmWCU8bMvz+ilzMb2iePY9mI6PJaW\
        Qvpg3Ix8aNjCwCPqe8/Ws/zbn9wCLgC8TOYZrXzqYhrWc0+4SAO9L\
        sAm72alETouHZFvoKJyi/k8/xaVCzEPVO9zLxvdMriIc911BfVC0X\
        fIbhFgLrEcdpBHgJeBUZmjXQi/x9VyNhz+fJtmfxAuBh59wWxMl06\
        QJeID7duT04vJE2jTfdp0EFUsvMVsgkZCSL7pr6JemdcZWT7zBw0V\
        hGrUcchfD4jMohulecvANUjvLU88dqodab+k6SO5Y/5OSZAvzp5Hk\
        yizFzgUNOwYGUfPc5eU4hszFp9AJ7gnw/IpPtrYi7uqSfyvtHDhC/\
        vvuJP8tfdtJ3I50oE8tJ3kHLIunTkOUu0fS1KfVcCWxj/NN42gjXh\
        4WO5d0peXoQJy16jZ8J0manpC2u1YjQEwyPYWBmkPaOk7aL+NDsTu\
        NtQrZbN8p0Izf8MeQavksySLKa5DN2JvCmc35zPQZMo/zyHh2q+5x\
        zo0hPjRJGdz4Frqun8RYiDO68lZI2GdkiN3q9tyLP8vD3Q8CF9TZ+\
        L9IDow0cd35fnlLuDsQpsNUQ2an0LHZ9Hfd4arwNv16l8vfGW7mRi\
        XA5knvU5FhVohuZ/3QrP4D9h0CjuIzkyFlCFj/kwtsple9FxDcawz\
        ri139HlkJZVvTfTzJ0BuJYpb0aGcVw0Pn9SJZCYwk8A9hYJX0lcFe\
        Whgw/VBO4DXHdo2HKQeB9J88byHuvMcFYSXzMH0He2WYhYbZoWpZZ\
        EmN8PE38mg+Op7L5lCMs4fFIJP0xkk5Xq8aXG0VuAnciC8mjlX2Qk\
        m/IyTOMhSOLZAkSPg6PZ+utaC3pQ7PLHMpLbKrdCIZH3FBiO/JaFA\
        167yN9NQHA9ST/F2iIjC68YRiGUY3/ARxUpOOUQIkQAAAAAElFTkS\
        uQmCC"

coordimg = PhotoImage(data=coords)
image = Label(window, image=coordimg)
image.place(x=975, rely=0.825, anchor="c")

# ****** Define Default 3D Printing Options and View Type ******

view = StringVar()
view.set('hide')
# Dimensions of the print bed in mm
xdim = DoubleVar()
xdim.set(8*25.4)
ydim = DoubleVar()
ydim.set(6*25.4)
zdim = DoubleVar()
zdim.set(8*25.4)
# Slice step size in mm
slice_size = DoubleVar()
slice_size.set(0.5*25.4)

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
menu.add_cascade(label="Edit", menu=subMenu)
viewMenu = Menu(subMenu, tearoff=False)
subMenu.add_cascade(label="View Type", menu=viewMenu)
viewMenu.add_radiobutton(label='Wireframe', variable=view, value='wire')  # Full wireframe
viewMenu.add_radiobutton(label='Hide Faces', variable=view, value='hide')  # Hide non-visible faces
viewMenu.add_radiobutton(label='Partial Hidden', variable=view, value='grey')  # Grey hidden lines
subMenu.add_command(label="Slicer Settings", command=save_click)

# Create "Help" submenu
subMenu = Menu(menu, tearoff=False)
menu.add_cascade(label="Slicer", menu=subMenu)
subMenu.add_command(label="Run Slicer", command=lambda: DrawObject.slice_geometry(file_select.stlobject))

# Create "Help" submenu
subMenu = Menu(menu, tearoff=False)
menu.add_cascade(label="Help", menu=subMenu)
subMenu.add_command(label="About", command=about_popup)

# ****** Control Panel ******

# Control text labels
orientation = Label(window, text="Print Orientation", font=("Helvetica", 16))
orientation.place(x=975, rely=0.075, anchor="c")
xaxis = Label(window, text="X", font=("Helvetica", 16))
xaxis.place(x=975, rely=0.2, anchor="c")
yaxis = Label(window, text="Y", font=("Helvetica", 16))
yaxis.place(x=975, rely=0.40, anchor="c")
zaxis = Label(window, text="Z", font=("Helvetica", 16))
zaxis.place(x=975, rely=0.6, anchor="c")

# Rotation buttons layout
x_l = Button(window, text="<-", width=5, command=lambda: DrawObject.plot_transform(file_select.stlobject, screen,
                                                                                   'rotation', [3, -90]))
x_l.place(x=925, rely=.2, anchor="c")
x_r = Button(window, text="->", width=5, command=lambda: DrawObject.plot_transform(file_select.stlobject, screen,
                                                                                   'rotation', [3, 90]))
x_r.place(x=1025, rely=.2, anchor="c")
y_l = Button(window, text="<-", width=5, command=lambda: DrawObject.plot_transform(file_select.stlobject, screen,
                                                                                   'rotation', [1, -90]))
y_l.place(x=925, rely=.40, anchor="c")
y_r = Button(window, text="->", width=5, command=lambda: DrawObject.plot_transform(file_select.stlobject, screen,
                                                                                   'rotation', [1, 90]))
y_r.place(x=1025, rely=.40, anchor="c")
z_l = Button(window, text="<-", width=5, command=lambda: DrawObject.plot_transform(file_select.stlobject, screen,
                                                                                   'rotation', [2, 90]))
z_l.place(x=925, rely=.6, anchor="c")
z_r = Button(window, text="->", width=5, command=lambda: DrawObject.plot_transform(file_select.stlobject, screen,
                                                                                   'rotation', [2, -90]))
z_r.place(x=1025, rely=.6, anchor="c")

# ****** Status Bar ******

status = Label(window, text="Waiting...", bd=1, relief=SUNKEN, anchor=W)
status.pack(side=BOTTOM, fill=X)

# ****** Run Main GUI Loop ******

window.mainloop()  # Main loop to run the GUI, waits for button input
