from flask import Flask, request, jsonify, render_template
from pathlib import Path

import numpy
from PIL import Image

app = Flask(__name__)


data_folder = Path(__file__).absolute().parent.joinpath("data")
im = Image.open(data_folder.joinpath("ASTGTMV003_S45E168_dem.tif"))
imarray = numpy.array(im)


@app.route("/height/<int:col_min>/<int:row_min>/<int:col_max>/<int:row_max>")
def height(col_min, row_min, col_max, row_max):
    assert col_max < imarray.shape[0]
    assert row_max < imarray.shape[1]

    return jsonify({"height": imarray[col_min:col_max, row_min:row_max].tolist()})


if __name__ == "__main__":
    app.run()
