import svgwrite
import csv

'''
Codes generate a print head path from a contour data set a specific z-level
 - svgcreate: create an SVG file composed of line segments connecting each of the point pairs on z slice
 - headpath: create a CSV file describing the position of the print in (X,Y,Z) coordinates and whether the extruder 
             should be turned on when moving to that location

Evan Chodora, 2018
https://github.com/evanchodora/stl-slicer
echodor@clemson.edu
'''


def svgcreate(pairs, z, ymax, fillx, filly):
    # Create a new SVG file with the file name as the z-coordinate of the slice
    dwg = svgwrite.Drawing('outputs/' + str(z) + '.svg', profile='tiny')

    # Create lines for the geometry segments sliced on the given z-plane
    for pair in pairs:
        # Offset the y position by ymax-y in order to account for the difference in SVG coordinate system (+Y is down)
        dwg.add(dwg.line((pair[0], ymax-pair[1]), (pair[2], ymax-pair[3]), stroke=svgwrite.rgb(0, 0, 0, "%")))
    # Create lines for
    for fill_line in fillx:
        # Loop over points for each fill line in x (always even number)
        for pts in range(int(len(fill_line[1])/2)):
            dwg.add(dwg.line((fill_line[0], ymax - fill_line[1][2*pts]), (fill_line[0], ymax - fill_line[1][2*pts+1]),
                             stroke=svgwrite.rgb(0, 0, 0, "%")))
    for fill_line in filly:
        # Loop over points for each fill line in y (always even number)
        for pts in range(int(len(fill_line[1])/2)):
            dwg.add(dwg.line((fill_line[1][2*pts], ymax - fill_line[0]), (fill_line[1][2*pts+1], ymax - fill_line[0]),
                             stroke=svgwrite.rgb(0, 0, 0, "%")))
    dwg.save()  # Save the SVG file to the output folder


def headpath(contour, z):
    # Create a path for the print head to follow based a supplied contour path
    if len(contour) != 0:
        contour_num = 1
        start = 1  # Indicates the start of a contour to handle contour looping
        begin = []
        # Open the path.csv file to append new lines, create it if it does not exist
        with open('outputs/path.csv', 'a', newline='') as csvfile:
            path_writer = csv.writer(csvfile, delimiter=' ', quotechar='|', quoting=csv.QUOTE_MINIMAL)
            # Loop over the contour segments
            for segment in contour:
                if segment[4] == contour_num:
                    if start == 1:
                        begin = [segment[0], segment[1]]
                        row = [segment[0], segment[1], z, 0]
                        path_writer.writerow(row)
                        start = 0
                    else:
                        row = [segment[0], segment[1], z, 1]
                        path_writer.writerow(row)
                else:
                    # Add the beginning coordinate to the end of a contour to complete the contour
                    contour_num = segment[4]
                    row1 = [begin[0], begin[1], z, 1]
                    row2 = [segment[0], segment[1], z, 0]
                    path_writer.writerow(row1)
                    path_writer.writerow(row2)
    return
