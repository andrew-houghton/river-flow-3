import pyproj
import rasterio
from pathlib import Path


start_point = (147.086086,-41.448218)
end_point = (147.122328,-41.443116)
proj_string = "+proj=utm +zone=55 +south +datum=WGS84 +units=m +no_defs"

def lat_lon_to_row_col(point):
    pass

def row_col_to_lat_lon(rowcol):

def start_finish_to_path(start_point, end_point):
    # Returns a list of lat longs with heights

    start_rowcol = lat_lon_to_row_col(start_point)
    end_rowcol = lat_lon_to_row_col(end_point)
    size_factors = [0,0,0,0]
    return enlarge_bounding_box_until_path_is_found(start_rowcol, end_rowcol, size_factors)

def apply_window_to_rowcol(window, rowcol):
    # Convert co-ordinates to be relative to a window
    pass

def get_raster(window, map_type="height"):
    if map_type == "height":
        pass
    else:
        pass

def enlarge_bounding_box_until_path_is_found(start_rowcol, end_rowcol, size_factors):
    window = generate_bounding_box(start_rowcol, end_rowcol, size_factors)
    start_window_rowcol = apply_window_to_rowcol(start_rowcol)
    end_window_rowcol = apply_window_to_rowcol(end_rowcol)
    height_raster = get_raster(window)
    graph = convert_to_graph(height_raster)
    graph = merge_equal_height(graph)
    graph = flood_low_points(graph)

    # Starting from start_window_rowcol start tracing a path
    # If there is branching select the lower point
    # If there is a tie select the further point (manhattan distance)
    # If there is still a tie then select at random
    # Move to next point and continue tracing the path

    # Finishing:
    # while distance to end is within a threshold then add current end point as a candidate
    # if distance ever goes back above the threshold then pick the best end candidate
    # if the path hits the end then exit early

    path = [start_window_rowcol]
    for i in range(100):
        last_point = path[-1]
        next_points = graph[last_point]
        lowest_point = next_points[0]
        

    return trace_path(height_raster, start_window_rowcol, end_window_rowcol)

def generate_bounding_box(start_rowcol, end_rowcol, size_factors):
    # Generate a box which encloses the start and end point
    # Size factors stores where the bounding box needs to be larger than normal
    pass
