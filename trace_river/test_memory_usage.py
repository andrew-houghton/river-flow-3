import rasterio as rio
from pathlib import Path
from matplotlib import pyplot as plt
import numpy as np
from memory_profiler import profile
from matplotlib import pyplot as plt


heights_tif_path = (
    Path(__name__).absolute().parent.parent.joinpath("tasmania", "heights.tif")
)


def get_raster(window, map_type="height"):
    if map_type == "height":
        with rio.open(heights_tif_path) as heights:
            return heights.read(1, window=window)
    else:
        raise Exception("Not implemented")


def main():
    heights = np.zeros((30978, 30978))

    window = rio.windows.Window(col_off=2200, row_off=2200, width=100, height=100)
    raster = get_raster(window)

    heights[200:300, 200:300] = raster

    plt.imshow(heights[200:300, 200:300])
    plt.show()


if __name__ == "__main__":
    main()
