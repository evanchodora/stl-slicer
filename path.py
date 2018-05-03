import svgwrite
import csv
import math
import os

'''
Codes generate a print head path from a contour data set a specific z-level
 - svgcreate: create an SVG file composed of line segments connecting each of the point pairs on z slice
 - headpath: create a CSV file describing the position of the print in (X,Y,Z) coordinates and whether the extruder 
             should be turned on when moving to that location (outline and infill pattern)
 - time_calc: append the total elapsed time to the headpath CSV file to show the total elapsed time and the time at 
              each point

Evan Chodora, 2018
https://github.com/evanchodora/stl-slicer
echodor@clemson.edu
'''


def svgcreate(pairs, z, ymax, fillx, filly):
    # Create a new SVG file with the file name as the z-coordinate (inches) of the slice (round to 0.001 in)
    dwg = svgwrite.Drawing('outputs/' + str(round(z/25.4, 3)) + '.svg')

    # Create lines for the geometry segment point pairs sliced on the given z-plane
    for pair in pairs:
        # Offset the y position by ymax-y in order to account for the difference in SVG coordinate system (+Y is down)
        dwg.add(dwg.line((pair[0], ymax-pair[1]), (pair[2], ymax-pair[3]), stroke=svgwrite.rgb(0, 0, 0, "%")))
    # Create lines for infill parallel to the Y axis
    for fill_line in fillx:
        # Loop over points for each fill line in X (always even number)
        for pts in range(int(len(fill_line[1])/2)):
            dwg.add(dwg.line((fill_line[0], ymax - fill_line[1][2*pts]), (fill_line[0], ymax - fill_line[1][2*pts+1]),
                             stroke=svgwrite.rgb(0, 0, 0, "%")))
    # Create lines for infill parallel to the X axis
    for fill_line in filly:
        # Loop over points for each fill line in Y (always even number)
        for pts in range(int(len(fill_line[1])/2)):
            dwg.add(dwg.line((fill_line[1][2*pts], ymax - fill_line[0]), (fill_line[1][2*pts+1], ymax - fill_line[0]),
                             stroke=svgwrite.rgb(0, 0, 0, "%")))
    dwg.save()  # Save the SVG file to the output folder


def headpath(contour, fillx, filly, z):
    # Create a path for the print head to follow based a supplied contour path
    # Format = [ X, Y, Z, On/Off]
    # On/Off denoted by a 1 or 0, respectively
    # 1 = extruder printing when moving to that coordinate from previous print head position
    # 0 = extruder off when moving to that coordinate from previous print head position

    c = 25.4  # Conversion from mm to in
    d = 4  # Number of decimals places to round the coordinates (0.0001 in)

    if len(contour) != 0:
        contour_num = 1  # Start with the first (possibly the only contour on that slice)
        start = 1  # Indicates the start of a contour to handle contour looping
        begin = []
        # Open the path.csv file to append new lines, create it if it does not exist
        with open('outputs/path.csv', 'a', newline='') as csvfile:
            path_writer = csv.writer(csvfile, delimiter=' ', quotechar='|', quoting=csv.QUOTE_MINIMAL)
            # Loop over the contour segments
            for segment in contour:
                # Check whether this segment is a part of the current contour loop
                if segment[4] == contour_num:
                    # If it is the first point on that contour:
                    if start == 1:
                        begin = [segment[0], segment[1]]  # Store the start of the contour
                        row = [round(segment[0]/c, d), round(segment[1]/c, d), round(z/c, d), 0]  # Head off when moving
                        path_writer.writerow(row)
                        start = 0  # Next point is no longer first of contour
                    else:
                        row = [round(segment[0]/c, d), round(segment[1]/c, d), round(z/c, d), 1]  # Extruding contour
                        path_writer.writerow(row)
                # If this is a new contour:
                else:
                    # Add the beginning coordinate to the end of a contour to complete the contour
                    contour_num = segment[4]  # Update contour number
                    row1 = [round(begin[0]/c, d), round(begin[1]/c, d), round(z/c, d), 1]  # End of previous contour
                    row2 = [round(segment[0]/c, d), round(segment[1]/c, d), round(z/c, d), 0]  # Start of next contour
                    path_writer.writerow(row1)
                    path_writer.writerow(row2)
                    begin = [segment[0], segment[1]]  # Store the start of the next contour
            # Write the last stored begin point to the end of the contour to print the entire loop for the slice
            row = [round(begin[0]/c, d), round(begin[1]/c, d), round(z/c, d), 1]
            path_writer.writerow(row)

            # Print the position directions for the calculated infill patterns
            for fill_line in fillx:
                # Loop over points for each fill line in X (always even number)
                for pts in range(int(len(fill_line[1])/2)):
                    # Move to first point in infill line and extrude when moving to the second
                    row1 = [round(fill_line[0]/c, d), round(fill_line[1][2*pts]/c, d), round(z/c, d), 0]
                    row2 = [round(fill_line[0]/c, d), round(fill_line[1][2*pts+1]/c, d), round(z/c, d), 1]
                    path_writer.writerow(row1)
                    path_writer.writerow(row2)
            for fill_line in filly:
                # Loop over points for each fill line in Y (always even number)
                for pts in range(int(len(fill_line[1]) / 2)):
                    # Move to first point in infill line and extrude when moving to the second
                    row1 = [round(fill_line[1][2*pts]/c, d), round(fill_line[0]/c, d), round(z/c, d), 0]
                    row2 = [round(fill_line[1][2*pts+1]/c, d), round(fill_line[0]/c, d), round(z/c, d), 1]
                    path_writer.writerow(row1)
                    path_writer.writerow(row2)

    return


def time_calc(speed):
    # Calculate the time corresponding to the location of the print head at each point in the path CSV file
    # Speed input into the function based on machine specifications
    d = 4  # Decimal places to round time

    # Open the generated CSV file and open a new temporary CSV file
    with open('outputs/path.csv', 'r') as csvfile, open('outputs/path_temp.csv', 'w', newline='') as outfile:
        reader = csv.reader(csvfile, delimiter=',', quoting=csv.QUOTE_NONE)
        writer = csv.writer(outfile, delimiter=' ')

        previous_line = []  # Initialize variable to track the coordinates of the previous line
        start = 0  # Variable to indicate if the point is the first in the file
        for line in reader:
            # Convert read text string to float variables
            line = line[0].split()
            line = [float(i) for i in line]
            if start != 0:
                pre_row = previous_line
                pre_time = pre_row[0]
                p_x, p_y, p_z = pre_row[1], pre_row[2], pre_row[3]
                n_x, n_y, n_z = line[0], line[1], line[2]
                # Calculate the distance from one point to the next
                dist = math.sqrt((n_x-p_x)**2 + (n_y-p_y)**2 + (n_z-p_z)**2)
                # Calculate the time to move that distance based on the applied speed
                time = round(pre_time + (dist/speed), d)
            else:
                time = 0  # Time at start is 0
                start = 1

            # Create new row for the CSV file and write to the file
            row = [time, line[0], line[1], line[2], line[3]]
            writer.writerow(row)
            previous_line = row  # Update the previous line for the next calculation

    # Remove the old file and rename the temporary file
    os.remove('outputs/path.csv')
    os.rename('outputs/path_temp.csv', 'outputs/path.csv')

    return
