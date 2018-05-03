import numpy as np
import gtransform
from math import isinf

'''
Codes to slice geometry at a given value Z (height above the print bed)
Functions:
 - geom_to_bed_coords: moves geometry from origin for screen plotting to bed surface (Z=0)
 - interpolation: interpolates between 2 points in 3D space based on a specific Z value between the points
 - compute_points_on_z: converts each STL face that is cut by the Z slice to a pair of points to build an outer contour
 - build_contours: converts the previously calculated discontinous point pairs into sets of continous contours
 - infill: calculates the start and stop points for grid infill lines filling in the previously calculated contours

Evan Chodora, 2018
https://github.com/evanchodora/stl-slicer
echodor@clemson.edu
'''


def geom_to_bed_coords(geometry, xdim, ydim, zdim):
    # Rescale object geometry to the size of the print bed volume and translate from the origin to the center of the
    # print bed. The object plotted on the screen is larger for visual representation and centered at the origin in
    # order to conduct object rotations naturally

    max_size = np.max(geometry, axis=0)  # Max X,Y,Z values of the object
    # Scale geometry to fit within the bed dimensions (convert from viewing size to actual)
    scale = min(xdim/(2*max_size[0]), ydim/(2*max_size[1]), zdim/(2*max_size[2]))
    geometry = gtransform.scale(geometry, 1/scale)  # Apply global scaling with appropriate factor
    max_size = np.max(geometry, axis=0)  # Max X,Y,Z values of the object
    geometry = gtransform.translate(geometry, xdim/2, max_size[1], zdim/2)  # Translate object onto print bed surface

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
    geometry = np.around(geometry, 5)  # Round geometry data
    num_faces = int((geometry.shape[0]) / 3)  # Every 3 points represents a single face (length/3)
    geometry = geometry[:, 0:3]  # Specifically pull the X,Y,Z coordinates - ignore H
    points = []  # Initialize array of point pairs
    tol = 0.005  # Tolerance criteria for determining whether 2 points are unique (0.005 mm = 5 micron)
    for f in range(0, num_faces):  # Loop every each face in the geometry set
        pairs = []  # Initialize/clear point pair set for each face
        xy = [geometry[3*(f+1)-3].tolist(), geometry[3*(f+1)-2].tolist(), geometry[3*(f+1)-1].tolist()]
        # Store the 3 points that make up face "f" using lists of points
        # Remember: Screen Plotting = (X, Y, Z) and Printing Geometry = (Z, X, Y) so order needs to be adjusted here
        line = [[xy[0][2], xy[0][0], xy[0][1]],
                [xy[1][2], xy[1][0], xy[1][1]],
                [xy[2][2], xy[2][0], xy[2][1]]]

        # If a line segment bounds the Z slice plane:
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

        # If a point on the face exactly matches the Z slice plane
        if line[0][2] == z:
            pairs.append([line[0][0], line[0][1]])
        elif line[1][2] == z:
            pairs.append([line[1][0], line[1][1]])
        elif line[2][2] == z:
            pairs.append([line[2][0], line[2][1]])

        # Only need to keep point pairs (sets of 1 and 3 are not needed - these will be inherently handled by a point
        # pair from a face somewhere else in the object geometry)
        if len(pairs) == 2:
            # Reject points if they are the same (within tolerance) - too close together, not a path pair for printing
            if abs(pairs[0][0] - pairs[1][0]) < tol and abs(pairs[0][1] - pairs[1][1]) < tol:
                pass
            else:
                points.append(pairs)

    points = [item for sublist in points for item in sublist]  # Flatten list sets into an array
    edge_points = np.asarray(points).reshape((-1, 4))  # Reshape and convert to X1,Y1,X2,Y2 numpy array
    edge_points = np.around(edge_points, 5)  # Round these points

    return edge_points


def build_contours(edge_points):
    # Function to build continuous contours for point sets on the slice z
    contours = []  # Initialize contour point loop array
    contour_num = 1  # Initialize the count for the number of contours
    tol = 0.005  # Tolerance criteria for matching the next point in the contour
    points_left = edge_points  # Initialize points that are remaining = original points
    tail = []
    loop_cnt = 1  # Count number of times searched over the remaining points for geometry error handling
    while len(points_left) != 0:  # Loop over the point pairs and the index in the data array
        j = 1
        if not contours:  # First point pair needs to always be added to the contour data if variable is empty
            pair = points_left[0, :]
            contours.append([pair[0], pair[1], pair[2], pair[3], contour_num])
            tail = [pair[2], pair[3]]  # Tail is the second point of the line pair
            points_left = np.delete(points_left, 0, axis=0)  # Remove the point pair from the array of points
        while j <= len(points_left):
            pair = points_left[j-1, :]
            # If either point in that pair matches the tail from the previous head-tail pair:
            if abs(pair[0]-tail[0]) < tol and abs(pair[1]-tail[1]) < tol:
                contours.append([pair[0], pair[1], pair[2], pair[3], contour_num])
                points_left = np.delete(points_left, j-1, axis=0)  # Remove the point pair from the array of points
                tail = [pair[2], pair[3]]  # Tail is the second point of the line pair
                loop_cnt = 1  # Reset search loop counter
                break
            if abs(pair[2] - tail[0]) < tol and abs(pair[3] - tail[1]) < tol:
                contours.append([pair[2], pair[3], pair[0], pair[1], contour_num])
                points_left = np.delete(points_left, j-1, axis=0)  # Remove the point pair from the array of points
                tail = [pair[0], pair[1]]  # Tail is the second point of the line pair
                loop_cnt = 1  # Reset search loop counter
                break
            j = j + 1
        loop_cnt = loop_cnt + 1  # Increment loop search counter
        # If there are still points left and either the last point in the contour equals the first (completed loop) or
        # have unsuccessfully searched over all the points twice to find a match then create a new contour loop
        if (len(points_left) != 0 and abs(contours[0][0]-contours[-1][2]) < tol and
           abs(contours[0][1]-contours[-1][3]) < tol) or loop_cnt > 2*len(edge_points):
                contour_num = contour_num + 1  # Increment contour loop number
                pair = points_left[0, :]
                contours.append([pair[0], pair[1], pair[2], pair[3], contour_num])
                tail = [pair[2], pair[3]]  # Tail is the second point of the line pair
                points_left = np.delete(points_left, 0, axis=0)  # Remove the point pair from the array of points
    contours = np.asarray(contours).reshape((-1, 5))  # Reshape and convert to X1,Y1,X2,Y2,contour_num numpy array

    return contours


def infill(pairs, direct, spacing):
    # Function to compute the line infill spacing for the 3D printing
    # direction (direct): X-axis = 0 and Y-axis = 1
    fill = []

    if len(pairs) != 0:
        # Calculate max and min dimensions of the sliced points (in either X or Y)
        min_pos = min(np.min(pairs[:, direct]), np.min(pairs[:, direct+2]))
        max_pos = max(np.max(pairs[:, direct]), np.max(pairs[:, direct+2]))

        num_passes = int((max_pos - min_pos)/spacing)  # Number of infill lines to cover the object

        # Loop over the number of infill lines needed
        for fill_pass in range(num_passes+1):
            loc = min_pos + fill_pass*spacing  # Increment fill pass position by the infill spacing variable
            pts = []
            # Loop over each segment in the list of contour point pairs
            for segment in pairs:
                # If the line falls on either side of the current fill pass line position
                if segment[direct] < loc < segment[direct+2] or segment[direct+2] < loc < segment[direct]:
                    m = (segment[3]-segment[1])/(segment[2]-segment[0])  # Calculate the slope of the line
                    # Fill lines at x-locations
                    if direct == 0:
                        pts.append(m * (loc - segment[direct]) + segment[direct+1])  # y = m(x_loc-x1)+y1
                    # Fill lines at y-locations
                    else:
                        # Check if the slope is infinite (#/0)
                        if isinf(m):
                            pts.append(segment[direct+1])  # Intercept at either x-location of the segment (pick 2nd)
                        else:
                            pts.append((loc-segment[direct])/m + segment[direct-1])  # x = (y_loc-y1)/m + x1
            pts.sort()  # Sort points in order to construct infill path lines
            fill.append((loc, pts))  # Append to fill path list

    return fill
