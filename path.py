import svgwrite

'''
Codes generate a print head path from a contour data set a specific z-level
 - svgcreate: create an SVG file composed of line segments connecting each of the point pairs on z slice

Evan Chodora, 2018
https://github.com/evanchodora/viewer
echodor@clemson.edu
'''


def svgcreate(pairs, z, ymax):
    # Create a new SVG file with the file name as the z-coordinate of the slice
    dwg = svgwrite.Drawing('outputs/' + str(z) + '.svg', profile='tiny')
    for pair in pairs:
        # Offset the y position by ymax-y in order to account for the difference in SVG coordinate system (+Y is down)
        dwg.add(dwg.line((pair[0], ymax-pair[1]), (pair[2], ymax-pair[3]), stroke=svgwrite.rgb(0, 0, 0, "%")))
    dwg.save()  # Save the SVG file to the output folder
