from pathlib import Path
from PIL import Image


crop_file = 'LC08_L1TP_076091_20191111_20191115_01_T1.jpg'
crop_filepath = Path(__file__).absolute().parent.parent.joinpath('data', crop_file)

print("Loading file")
im = Image.open(crop_filepath)

print("Cropping")
w, h = im.size
crop_left = 12
crop_right = 22
crop_top = 12
crop_bottom = 3
im = im.crop((crop_left, crop_top, w-crop_right, h-crop_bottom))

print("Saving file")
im.save(crop_filepath)
