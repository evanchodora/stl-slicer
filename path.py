import numpy as np
import svgwrite

'''
Codes generate a print head path from a contour data set a specific z-level

Evan Chodora, 2018
https://github.com/evanchodora/viewer
echodor@clemson.edu
'''


def svgcreate(pairs, z):
    dwg = svgwrite.Drawing('outputs/' + str(z) + '.svg', profile='tiny')
    for pair in pairs:
        dwg.add(dwg.line((pair[0], pair[1]), (pair[2], pair[3]), stroke=svgwrite.rgb(0, 0, 0, "%")))
    dwg.save()
