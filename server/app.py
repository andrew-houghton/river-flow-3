from flask import Flask
from PIL import Image
from pathlib import Path
import rasterio as rio
from flask import send_file
from flask import jsonify
from random import randint
import numpy as np
import io


app = Flask(__name__)

heights_tif_path = (
    Path(__name__).absolute().parent.parent.joinpath("tasmania", "heights.tif")
)
colour_tif_path = (
    Path(__name__).absolute().parent.parent.joinpath("tasmania", "colour.tif")
)
CANVAS_WIDTH = 30978
CANVAS_HEIGHT = 30978
# min_height_value = -86
# max_height_value = 1610


@app.route("/")
def hello_world():
    return "Hello, World!"


@app.route(
    "/colour/<int:width>/<int:height>",
    defaults={"left_offset": None, "top_offset": None},
)
@app.route("/colour/<int:width>/<int:height>/<int:left_offset>/<int:top_offset>")
def colour(width, height, left_offset, top_offset):
    with rio.open(colour_tif_path) as colour_src:
        if left_offset is None:
            left_offset = randint(0, CANVAS_WIDTH - width - 1)
        if top_offset is None:
            top_offset = randint(0, CANVAS_HEIGHT - height - 1)
        w = rio.windows.Window(left_offset, top_offset, width, height)

        rgbArray = np.zeros((width, height, 3), "uint8")
        rgbArray[..., 0] = colour_src.read(1, window=w)
        rgbArray[..., 1] = colour_src.read(2, window=w)
        rgbArray[..., 2] = colour_src.read(3, window=w)

        file_object = io.BytesIO()
        pil_img = Image.fromarray(rgbArray)
        pil_img.save(file_object, "PNG")
        file_object.seek(0)
        return send_file(file_object, mimetype="image/png")


@app.route(
    "/height_image/<int:width>/<int:height>",
    defaults={"left_offset": None, "top_offset": None},
)
@app.route("/height_image/<int:width>/<int:height>/<int:left_offset>/<int:top_offset>")
def height_image(width, height, left_offset, top_offset):
    with rio.open(heights_tif_path) as heights_src:
        if left_offset is None:
            left_offset = randint(0, CANVAS_WIDTH - width - 1)
        if top_offset is None:
            top_offset = randint(0, CANVAS_HEIGHT - height - 1)
        w = rio.windows.Window(left_offset, top_offset, width, height)

        file_object = io.BytesIO()
        height_values = heights_src.read(1, window=w)
        min_height = height_values.min()

        # Rescale Heights
        height_range = height_values.max() - min_height
        height_values -= min_height
        height_values = height_values / height_range * 255
        height_values = height_values.astype("uint8")

        pil_img = Image.fromarray(height_values)
        pil_img.save(file_object, "PNG")
        file_object.seek(0)
        return send_file(file_object, mimetype="image/png")


@app.route(
    "/height/<int:width>/<int:height>",
    defaults={"left_offset": None, "top_offset": None},
)
@app.route("/height/<int:width>/<int:height>/<int:left_offset>/<int:top_offset>")
def height(width, height, left_offset, top_offset):
    with rio.open(heights_tif_path) as heights_src:
        if left_offset is None:
            left_offset = randint(0, CANVAS_WIDTH - width - 1)
        if top_offset is None:
            top_offset = randint(0, CANVAS_HEIGHT - height - 1)
        w = rio.windows.Window(left_offset, top_offset, width, height)
        height_values = heights_src.read(1, window=w)
        return jsonify(height_values.tolist())


if __name__ == "__main__":
    app.run(debug=True)
