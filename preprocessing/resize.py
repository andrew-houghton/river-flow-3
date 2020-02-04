from pathlib import Path
from PIL import Image

# Input images
target_size = (3601, 3601)
target_north = -43.9998611
target_east = 169.0001389
target_south = -45.0001389
target_west = 167.9998611

source_north = -43.54087
source_east = 169.80198
source_south = -45.67276
source_west = 166.82271

# Open the target file
source_file = "LC08_L1TP_076091_20191111_20191115_01_T1.jpg"
source_filepath = Path(__file__).absolute().parent.parent.joinpath("data", source_file)
save_file = 'true_colour_resized.jpg'
save_filepath = Path(__file__).absolute().parent.parent.joinpath('data', save_file)

im = Image.open(source_filepath)

# Find height and width of source
source_width, source_height = im.size
source_long = source_east - source_west
source_lat = source_north - source_south

# Find what portion of the height and width you should keep
crop_left = int(source_width * (target_west - source_west) / source_long)
crop_right = int(source_width * (target_east - source_west) / source_long)
crop_top = int(source_height * (source_north - target_north) / source_lat)
crop_bottom = int(source_height * (source_north - target_south) / source_lat)

# Crop file
im = im.crop((crop_left, crop_top, crop_right, crop_bottom))

# Resize cropped image to match other file
im = im.resize(target_size)

print("Saving file")
im.save(save_filepath)
