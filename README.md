# stl-slicer

Python-based STL slicer for generating line paths for 3D printing

Program designed to open and view ASCII STL files and then slice them for 3D printing operations. Supports variable 
slice heights and spacing between infill grid lines. Geometry moved to fit within a 8x8x6 inch print bed as large as
possible according to the part orientation.

Output files consist of an SVG file for each slice of the model showing the model outlines and the infill pattern and a
CSV file that lists the coordinates of the print head at different times and whether or not the extruder is on during
the move to that position.

Freeze using PyInstaller: ```pyinstaller.exe --onefile --windowed --icon=cube.ico Slicer.py```
