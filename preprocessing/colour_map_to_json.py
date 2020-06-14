from pathlib import Path
from PIL import Image
import json
import numpy

im = Image.open(Path(__file__).absolute().parent.joinpath('gist_earth.png'))
data = [[int(i[0]), int(i[1]), int(i[2])] for i in numpy.array(im)[0]]
json.dump(data, open('gist_earth.json', 'w'))
