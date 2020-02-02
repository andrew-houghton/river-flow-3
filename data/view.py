from PIL import Image
import numpy


im = Image.open('ASTGTMV003_S45E168_dem.tif')
imarray = numpy.array(im)
print(imarray.shape)
print(imarray.size)

print(imarray.dtype)
print(imarray.min())
print(imarray.max())
imarray = imarray//(imarray.max()/256)
print(imarray.dtype)
print(imarray.min())
print(imarray.max())
imarray = imarray.astype('int32')
print(imarray.dtype)

im2 = Image.fromarray(imarray)
im2.show()
im2.convert("RGB").save('ASTGTMV003_S45E168_dem.png')
