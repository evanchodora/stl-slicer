import numpy as np
import math as m

'''
Functions for the various geometric transformations and perspectives
 - Translation (X, Y, Z)
 - Rotation (about all 3 axes)
 - Global scaling (s value)
 - Perspective (isometric, dimetric, trimetric) with user-defined settings
 - Orthographic views (6)

Evan Chodora, 2018
https://github.com/evanchodora/viewer
echodor@clemson.edu
'''


# Determine the transform that should be applied to the geometry (data is specific data for each transformation)
def transform(geometry, normals, transtype, data):
        if transtype == 'translate':
                geometry = translate(geometry, data[0], data[1], data[2])
        if transtype == 'rotation':
                geometry, normals = rotation(geometry, normals, data[0], data[1])
        if transtype == 'zoom':
                geometry = scale(geometry, data[0])
        if transtype == 'ortho':
                geometry, normals = ortho(geometry, normals, data)
        return geometry, normals


# Translate geometry by x, y, z
def translate(geometry, x, y, z):
        geometry = geometry.dot(np.array([[1.0, 0.0, 0.0, 0.0],
                                          [0.0, 1.0, 0.0, 0.0],
                                          [0.0, 0.0, 1.0, 0.0],
                                          [x, y, z, 1.0]]))
        return geometry


# Scale geometry globally
def scale(geometry, s):
        scale_mat = np.array([[1.0, 0.0, 0.0, 0.0],
                              [0.0, 1.0, 0.0, 0.0],
                              [0.0, 0.0, 1.0, 0.0],
                              [0.0, 0.0, 0.0, s]])
        scale_mat = scale_mat/s  # Normalize such that s = 1 in the transformation matrix
        geometry = geometry.dot(scale_mat)
        return geometry


# Rotate geometry and the object outward normals about x, y, or z by an angle (in degrees)
def rotation(geometry, normals, axis, ang):
        ang = m.radians(ang)  # Convert angle to radians for computation
        s = m.sin(ang)  # sine (radians)
        c = m.cos(ang)  # cosine (radians)

        if axis == 1:  # Rotation about x-axis
                geometry = geometry.dot(np.array([[1.0, 0.0,  0.0, 0.0],
                                                  [0.0, c,    s,   0.0],
                                                  [0.0, -1*s, c,   0.0],
                                                  [0.0, 0.0,  0.0, 1.0]]))
                normals = normals.dot(np.array([[1.0, 0.0,  0.0, 0.0],
                                                [0.0, c,    s,   0.0],
                                                [0.0, -1*s, c,   0.0],
                                                [0.0, 0.0,  0.0, 1.0]]))
        if axis == 2:  # Rotation about y-axis
                geometry = geometry.dot(np.array([[c,   0.0, -1*s, 0.0],
                                                  [0.0, 1.0, 0.0,  0.0],
                                                  [s,   0.0, c,    0.0],
                                                  [0.0, 0.0, 0.0,  1.0]]))
                normals = normals.dot(np.array([[c,   0.0, -1*s, 0.0],
                                                [0.0, 1.0, 0.0,  0.0],
                                                [s,   0.0, c,    0.0],
                                                [0.0, 0.0, 0.0,  1.0]]))
        if axis == 3:  # Rotation about z-axis
                geometry = geometry.dot(np.array([[c,    s,   0.0, 0.0],
                                                  [-1*s, c,   0.0, 0.0],
                                                  [0.0,  0.0, 1.0, 0.0],
                                                  [0.0,  0.0, 0.0, 1.0]]))
                normals = normals.dot(np.array([[c,    s,   0.0, 0.0],
                                                [-1*s, c,   0.0, 0.0],
                                                [0.0,  0.0, 1.0, 0.0],
                                                [0.0,  0.0, 0.0, 1.0]]))
        return geometry, normals


# Flatten and rotate geometry according to type of orthographic view
def ortho(geometry, normals, view):
        mat = np.identity(4)  # Initialize transformation matrix

        # Determine which of the 6 orthographic views is requested and apply the transformation/rotation
        # Views are referenced according to the original geometry orientation (front = +Z, top = +Y, right = +X, etc.)
        if view == 'top':
                mat[1, 1] = 0
                geometry = np.dot(geometry, mat)
                geometry, normals = rotation(geometry, normals, 1, 90)
        if view == 'bottom':
                mat[1, 1] = 0
                geometry = np.dot(geometry, mat)
                geometry, normals = rotation(geometry, normals, 1, -90)
        if view == 'right':
                mat[0, 0] = 0
                geometry = np.dot(geometry, mat)
                geometry, normals = rotation(geometry, normals, 2, 90)
        if view == 'left':
                mat[0, 0] = 0
                geometry = np.dot(geometry, mat)
                geometry, normals = rotation(geometry, normals, 2, -90)
        if view == 'front':
                mat[2, 2] = 0
                geometry = np.dot(geometry, mat)
        if view == 'back':
                mat[2, 2] = 0
                geometry = np.dot(geometry, mat)
                geometry, normals = rotation(geometry, normals, 2, 180)
        return geometry, normals


# Project geometry with isometric projection
def perspective(persp, geometry, fz, phi, theta):

        if persp == 'iso':  # Isometric perspective (constant value for rotations - no variables)
                phi = m.radians(45)  # Rotation about Y
                theta = m.asin(m.tan(m.radians(30)))  # Rotation about X

        if persp == 'di':  # Dimetric perspective (based on passed fz value)
                theta = m.asin(fz/m.sqrt(2))  # Rotation about Y
                phi = m.asin(fz/m.sqrt(2-fz*fz))  # Rotation about X

        if persp == 'tri':  # Trimetric perspective (based on passed phi and theta values)
                phi = m.radians(phi)  # Rotation about Y
                theta = m.radians(theta)  # Rotation about X

        rot_1 = np.array([[m.cos(phi), 0.0, -1*m.sin(phi), 0.0],
                          [0.0,        1.0, 0.0,           0.0],
                          [m.sin(phi), 0.0, m.cos(phi),    0.0],
                          [0.0,        0.0, 0.0,           1.0]])
        rot_2 = np.array([[1.0, 0.0,             0.0,          0.0],
                          [0.0, m.cos(theta),    m.sin(theta), 0.0],
                          [0.0, -1*m.sin(theta), m.cos(theta), 0.0],
                          [0.0, 0.0,             0.0,          1.0]])
        flat = np.array([[1, 0, 0, 0],
                         [0, 1, 0, 0],
                         [0, 0, 0, 0],
                         [0, 0, 0, 1]])

        # Apply transformations to the geometry for the chosen perspective
        geometry = geometry.dot(rot_1)  # Rotation about Y
        geometry = geometry.dot(rot_2)  # Rotation about X
        geometry = geometry.dot(flat)  # Flatten to Z = 0

        # Apply same rotations to camera vector (but in the opposite order)
        camera = np.array([0, 0, -1, 1]).dot(rot_2)
        camera = camera.dot(rot_1)
        camera = np.array([camera[0], camera[1], -1*camera[2]])  # Camera vector for determining face orientation

        return geometry, camera
