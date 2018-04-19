import numpy as np
import gtransform
from math import isinf

'''
Codes to slice geometry at a given value Z (height above the print bed)

Evan Chodora, 2018
https://github.com/evanchodora/stl-slicer
echodor@clemson.edu
'''


def geom_to_bed_coords(geometry, xdim, ydim, zdim):
    # Rescale object geometry to the size of the print bed volume and translate from the origin to the center of the
    # print bed. The object plotted on the screen is larger for visual representation and centered at the origin in
    # order to conduct object rotations

    max_size = np.max(geometry, axis=0)  # Max X,Y,Z values of the object
    # Scale geometry to fit within the bed dimensions (convert from viewing size to actual)
    scale = min(xdim/(2*max_size[0]), ydim/(2*max_size[1]), zdim/(2*max_size[2]))
    geometry = gtransform.scale(geometry, 1/scale)  # Apply global scaling with appropriate factor
    max_size = np.max(geometry, axis=0)  # Max X,Y,Z values of the object
    geometry = gtransform.translate(geometry, xdim/2, max_size[1], zdim/2)  # Translate object into print bed center

    return geometry


def interpolation(p1, p2, slice_z):
    # Interpolate between points based on slice z value
    vector = (p2[0] - p1[0], p2[1] - p1[1], p2[2] - p1[2])  # Compute the vector between point 1 and 2 on the line in 3D
    rel_z = slice_z - p1[2]  # Relative z = height between slice z and the z of the lower point
    a = rel_z/vector[2]  # Parametric length along the vector
    points = [a * vector[0] + p1[0], a * vector[1] + p1[1]]  # Compute new X and Y points at that parametric length

    return points


def compute_points_on_z(geometry, z, xdim, ydim, zdim):
    # Compute the points on the z slice plane
    geometry = geom_to_bed_coords(geometry, xdim, ydim, zdim)  # Position and size geometry correctly
    geometry = np.around(geometry, 5)
    num_faces = int((geometry.shape[0]) / 3)  # Every 3 points represents a single face (length/3)
    geometry = geometry[:, 0:3]  # Specifically pull the X,Y,Z coordinates - ignore H
    points = []  # Initialize array of point pairs
    tol = 0.005
    for f in range(0, num_faces):  # Loop every each face in the geometry set
        pairs = []  # Initialize/clear point pair set for each face
        xy = [geometry[3*(f+1)-3].tolist(), geometry[3*(f+1)-2].tolist(), geometry[3*(f+1)-1].tolist()]
        # Store the 3 lines that make up face "f" using lists of points
        # Remember: Screen Plotting = (X, Y, Z) and Printing Geometry = (Z, X, Y)
        line = [[xy[0][2], xy[0][0], xy[0][1]],
                [xy[1][2], xy[1][0], xy[1][1]],
                [xy[2][2], xy[2][0], xy[2][1]]]

        # If a line segment bounds the z slice plane:
        if (line[1][2] < z < line[0][2]) or (line[0][2] < z < line[1][2]):
            p1 = [line[0][0], line[0][1], line[0][2]]
            p2 = [line[1][0], line[1][1], line[1][2]]
            pairs.append(interpolation(p1, p2, z))

        if (line[2][2] < z < line[0][2]) or (line[0][2] < z < line[2][2]):
            p1 = [line[0][0], line[0][1], line[0][2]]
            p2 = [line[2][0], line[2][1], line[2][2]]
            pairs.append(interpolation(p1, p2, z))

        if (line[2][2] < z < line[1][2]) or (line[1][2] < z < line[2][2]):
            p1 = [line[1][0], line[1][1], line[1][2]]
            p2 = [line[2][0], line[2][1], line[2][2]]
            pairs.append(interpolation(p1, p2, z))

        #
        if line[0][2] == z:
            pairs.append([line[0][0], line[0][1]])
        elif line[1][2] == z:
            pairs.append([line[1][0], line[1][1]])
        elif line[2][2] == z:
            pairs.append([line[2][0], line[2][1]])

        # Only need to keep point pairs (1 and 3 are not needed - handled by other vertices in the object)
        if len(pairs) == 2:
            # Reject points if they are the same (within tolerance) - not a path pair for printing
            if abs(pairs[0][0] - pairs[1][0]) < tol and abs(pairs[0][1] - pairs[1][1]) < tol:
                pass
            else:
                points.append(pairs)

    points = [item for sublist in points for item in sublist]  # Flatten list sets into an array
    edge_points = np.asarray(points).reshape((-1, 4))  # Reshape and convert to X1,Y1,X2,Y2 numpy array
    edge_points = np.around(edge_points, 5)

    return edge_points


def build_contours(edge_points):
    # Function to build continuous contours for point sets on the slice z
    contours = []  # Initialize contour point loop array
    contour_num = 1  # Initialize the count for the number of contours
    tol = 0.005  # Tolerance criteria for matching the next point in the contour
    points_left = edge_points  # Initialize points that are remaining = original points
    tail = []
    loop_cnt = 1  # Count number of times searhced over the remaining points for geometry error handling
    while len(points_left) != 0:  # Loop over the point pairs and the index in the data array
        j = 1
        if not contours:  # First point pair needs to be added to the contour data if variable is empty
            pair = points_left[0, :]
            contours.append([pair[0], pair[1], pair[2], pair[3], contour_num])
            tail = [pair[2], pair[3]]  # Tail is the second point of the line pair
            points_left = np.delete(points_left, 0, axis=0)  # Remove the point pair from the array of points
        while j <= len(points_left):
            pair = points_left[j-1, :]
            if abs(pair[0]-tail[0]) < tol and abs(pair[1]-tail[1]) < tol:
                contours.append([pair[0], pair[1], pair[2], pair[3], contour_num])
                points_left = np.delete(points_left, j-1, axis=0)
                tail = [pair[2], pair[3]]  # Tail is the second point of the line pair
                loop_cnt = 1
                break
            if abs(pair[2] - tail[0]) < tol and abs(pair[3] - tail[1]) < tol:
                contours.append([pair[2], pair[3], pair[0], pair[1], contour_num])
                points_left = np.delete(points_left, j-1, axis=0)
                tail = [pair[0], pair[1]]  # Tail is the second point of the line pair
                loop_cnt = 1
                break
            j = j + 1
        loop_cnt = loop_cnt + 1
        if (len(points_left) != 0 and abs(contours[0][0]-contours[-1][2]) < tol and
           abs(contours[0][1]-contours[-1][3]) < tol) or loop_cnt > 2*len(edge_points):
                contour_num = contour_num + 1
                pair = points_left[0, :]
                contours.append([pair[0], pair[1], pair[2], pair[3], contour_num])
                tail = [pair[2], pair[3]]  # Tail is the second point of the line pair
                points_left = np.delete(points_left, 0, axis=0)  # Remove the point pair from the array of points
    contours = np.asarray(contours).reshape((-1, 5))  # Reshape and convert to X1,Y1,X2,Y2,contour_num numpy array

    return contours


def infill(pairs, dir, spacing):
    # Function to compute the line infill spacing for the 3D printing
    # direction: X=0, Y=1
    fill = []

    if len(pairs) != 0:
        # Calculate max and min dimensions of the sliced points
        min_pos = min(np.min(pairs[:, dir]), np.min(pairs[:, dir+2]))
        max_pos = max(np.max(pairs[:, dir]), np.max(pairs[:, dir+2]))

        num_passes = int((max_pos - min_pos)/spacing)  # Number of infill lines to cover the object

        for fill_pass in range(num_passes+1):
            loc = min_pos + fill_pass*spacing  # Increment fill pass position by the infill spacing variable
            pts = []
            for segment in pairs:
                if segment[dir] < loc < segment[dir+2] or segment[dir+2] < loc < segment[dir]:
                    m = (segment[3]-segment[1])/(segment[2]-segment[0])
                    # Fill lines at x-locations
                    if dir == 0:
                        pts.append(m * (loc - segment[dir]) + segment[dir + 1])  # y = m(x_loc-x1)+y1
                    # Fill lines at y-locations
                    else:
                        # Check if the slope is infinite (#/0)
                        if isinf(m):
                            pts.append(segment[dir+1])  # Intercept at either x-location of the segment
                        else:
                            pts.append((loc-segment[dir])/m + segment[dir-1])  # x = (y_loc-y1)/m + x1
            pts.sort()  # Sort points in order to construct infill path lines
            fill.append((loc, pts))  # Append to fill path list

    return fill
