import numpy as np
import gtransform

'''
Code to orient the initial geometry centered upon the geometric origin
Then scales the object to fit within a window of the width and height supplied based on an isometric perspective
and a supplied screen width and height in pixels

Evan Chodora, 2018
https://github.com/evanchodora/viewer
echodor@clemson.edu
'''


def to_origin(geometry):

    # Compute object dimensions and distance from the origin
    max_size = np.max(geometry, axis=0)  # Max X,Y,Z values of the object
    min_size = np.min(geometry, axis=0)  # Min X,Y,Z values of the object
    x_trans = 0 - 0.5*(max_size[0]+min_size[0])  # Avg X distance from the origin (center of the object)
    y_trans = 0 - 0.5*(max_size[1]+min_size[1])  # Avg Y distance from the origin (center of the object)
    z_trans = 0 - 0.5*(max_size[2]+min_size[2])  # Avg Z distance from the origin (center of the object)
    geometry = gtransform.translate(geometry, x_trans, y_trans, z_trans)  # Translate object accordingly to origin

    return geometry


def fit_bed(geometry, xdim, ydim, zdim):

    # Scale object to fit in printing space (8in x 8in x 6in)
    max_size = np.max(geometry, axis=0)  # Max X,Y,Z values of the object

    # Compute object scaling based on the minimum ratio between the print bed dimensions and the object size
    scale = min(xdim/max_size[0], ydim/max_size[1], zdim/max_size[2])
    geometry = gtransform.scale(geometry, 1 / scale)  # Apply global scaling with appropriate factor

    max_size = np.max(geometry, axis=0)  # Max X,Y,Z values of the object
    geometry = gtransform.translate(geometry, xdim/2, max_size[1], zdim/2)  # Translate object accordingly to origin

    return geometry
