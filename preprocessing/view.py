from pathlib import Path

import numpy
from PIL import Image

data_folder = Path(__file__).absolute().parent.parent.joinpath('data')
print("Loading file")
im = Image.open(data_folder.joinpath('ASTGTMV003_S45E168_dem.tif'))
imarray = numpy.array(im)
imarray = imarray//(imarray.max()/256)  # // is floor division operator
imarray = imarray.astype('int32')
im2 = Image.fromarray(imarray)
print("Displaying file")
im2.show()
print("Saving file")
im2.convert("RGB").save(data_folder.joinpath('ASTGTMV003_S45E168_dem.png'))
