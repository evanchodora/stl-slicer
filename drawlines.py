import numpy as np

'''
Code to draw lines between vertices of STL faces
 - Pass in the numpy array of vertices in form [x y z h]
 - Each row represents a point and every 3 rows represents a connected object face w/ associated normal vector
 - Clip lines using a line clipping algorithm (50px within each edge of the passed display screen resolution)
 - Draws lines using a version of the Bresenham's Line Algorithm between every face point

Evan Chodora, 2018
https://github.com/evanchodora/stl-slicer
echodor@clemson.edu
'''


def draw_lines(geometry, normal, camera, view):
    num_faces = int((geometry.shape[0])/3)  # Every 3 points represents a single face (length/3)
    geometry = np.around(geometry)  # Round geometry values to integer values for pixel mapping
    geometry = geometry.astype(int)  # Convert geometry matrix to integer data type
    geometry = geometry[:, 0:2]  # Specifically pull the X and Y coordinates - ignore Z and H
    points = []

    for f in range(0, num_faces):  # Loop every each face in the geometry set
        dot = np.dot(normal[f, 0:3], camera)  # Dot the outward surface normal with the camera vector

        # Determine whether face needs to be plotted
        # Only compute lines if face is camera facing or hidden line view type is selected
        if dot < 0.0 or view == 'wire' or view == 'grey':
            front = 1
            # If plotted but not camera-facing - must be for hidden views and rearwards
            if dot >= 0.0:
                front = 0
            # Store the three points for face "f"
            xy = [geometry[3*(f+1)-3].tolist(), geometry[3*(f+1)-2].tolist(), geometry[3*(f+1)-1].tolist()]
            # Store the 3 lines that make up face "f" using lists of points
            line = [[xy[0][0], xy[0][1], xy[1][0], xy[1][1]],
                    [xy[1][0], xy[1][1], xy[2][0], xy[2][1]],
                    [xy[2][0], xy[2][1], xy[0][0], xy[0][1]]]
            for l in [0, 1, 2]:  # Loop each of the 3 lines of a face
                # Clip each line of the face based on the clipping window
                x1, y1, x2, y2 = line[l][0], line[l][1], line[l][2], line[l][3]
                points.append(line_algo(x1, y1, x2, y2, front))

    points = [item for sublist in points for item in sublist]  # Flatten list sets into an array
    line_points = np.asarray(points).reshape((-1, 3))  # Reshape and convert to XY numpy array for plotting
    return line_points


def line_algo(x0, y0, x1, y1, front):
    # Calculate line points using an adapted version of the Bresenham's Line Algorithm
    # https://en.wikipedia.org/wiki/Bresenham%27s_line_algorithm
    # https://www.cs.helsinki.fi/group/goa/mallinnus/lines/bresenh.html

    coords = []

    # Determine if the line slope is steeper than 1
    toosteep = abs(y1-y0) > abs(x1-x0)

    if toosteep:  # Reflect line across Y=X to have slope where: -0.5 < m < 0.5
        x0, y0 = y0, x0
        x1, y1 = y1, x1

    if x0 > x1:  # Swap left and right X's so line increases in Y as X increases
        x0, x1 = x1, x0
        y0, y1 = y1, y0

    deltax = x1-x0  # Change in X
    deltay = y1-y0  # Change in Y

    error = int(deltax/2.0)
    # Calculate direction to step in Y
    ystep = 1 if y0 < y1 else -1

    y = y0  # Initial Y coordinate
    # Loop over X's between x0 and x1
    for x in range(int(x0), int(x1)+1):
        coord = [y, x, front] if toosteep else [x, y, front]  # If was steep reverse back, otherwise keep order
        coords.append(coord)  # Append new X,Y point with direction indicator
        error -= abs(deltay)
        if error < 0:
            y += ystep
            error += deltax
    return coords


def clipping(x1, y1, x2, y2, xmin, xmax, ymin, ymax):
        # Clip each line to the screen buffer dimensions (50px within display window on all edges)

        # Assign location codes - binary code-type grid for each location
        inside = 0  # 0000
        left = 1  # 0001
        right = 2  # 0010
        below = 4  # 0100
        above = 8  # 1000

        # Check the location condition of a given X and Y coordinate in reference to the clipping region
        def check_cond(xc, yc):
                code = inside  # Initialize state then use "bitwise or" to append the binary condition value
                if xc < xmin:
                        code |= left
                elif xc > xmax:
                        code |= right
                if yc < ymin:
                        code |= below
                elif yc > ymax:
                        code |= above
                return code  # Return location condition of the point

        code1 = check_cond(x1, y1)  # Check left endpoint of the line - determine where it is located
        code2 = check_cond(x2, y2)  # Check right endpoint of the line - determine where it is located
        x, y = [], []

        # While both points aren't already in the display area
        # If they initially are inside or are clipped inside, then break out and return new clipped endpoints to
        # save the computation of needing to do any more clipping
        while (code1 | code2) != 0:

                if (code1 & code2) != 0:  # If both points are outside of screen, reject both
                        return 9999, 9999, 9999, 9999  # Return condition to entirely skip point set when drawing lines
                else:
                        # Identify first point outside the region to begin clipping along the line
                        if code1 != 0:
                                code_out = code1  # x1,y1 outside region
                        else:
                                code_out = code2  # x2,y2 outside region
                        # Based on each condition move along the slope of each line (Line Clipping Algorithm)
                        if code_out & above:
                                x = x1 + (x2 - x1) * (ymax - y1) / (y2 - y1)
                                y = ymax
                        elif code_out & below:
                                x = x1 + (x2 - x1) * (ymin - y1) / (y2 - y1)
                                y = ymin
                        elif code_out & right:
                                y = y1 + (y2 - y1) * (xmax - x1) / (x2 - x1)
                                x = xmax
                        elif code_out & left:
                                y = y1 + (y2 - y1) * (xmin - x1) / (x2 - x1)
                                x = xmin
                        if code_out == code1:  # x1,y1 point was out of the region
                                x1 = x  # new X
                                y1 = y  # new Y
                                code1 = check_cond(x1, y1)  # Check condition of new point and loop
                        else:  # x2,y2 point was out of the region
                                x2 = x  # new X
                                y2 = y  # new Y
                                code2 = check_cond(x2, y2)  # Check condition of new point and loop
        # Return points that are within the clipping region for line drawing or with "9999" to ignore when drawing
        return x1, y1, x2, y2
