from vis_dataclasses import load_image_file_zipped
from pathlib import Path
from typing import Tuple
from dataclasses import dataclass
from PIL import Image
import pygame
import numpy as np
import rasterio as rio


def pil_image_to_surface(im):
    return pygame.image.fromstring(im.tobytes(), im.size, im.mode)


def calculate_scale_ratio(screen_size, image):
    return min(
        screen_dimension / original_dimension
        for screen_dimension, original_dimension in zip(reversed(screen_size), image.size)
    )


class VisSettings:
    def __init__(
        self,
        screen_size: Tuple[int, int],
        framerate: int = 165,
        selection_line_width: int = 3,
        selection_line_colour: Tuple[int, int, int] = (0, 204, 51),
    ):
        print("Loading data...")
        self.screen_size = screen_size
        self.pil_colour_image = load_image_file_zipped(str(Path(__name__).absolute().parent.parent.joinpath("tasmania", "colour.tif")))
        self.pil_small_colour_image = load_image_file_zipped(str(Path(__name__).absolute().parent.parent.joinpath("tasmania", "colour_small.png")))

        self.full_size_dimensions = self.pil_colour_image.size
        self.scale_ratio = calculate_scale_ratio(self.screen_size, self.pil_colour_image)
        small_image_scale_ratio = calculate_scale_ratio(self.screen_size, self.pil_small_colour_image)

        resized_dimensions = (small_image_scale_ratio * self.pil_small_colour_image.size[0], small_image_scale_ratio* self.pil_small_colour_image.size[1])
        self.pil_small_colour_image.thumbnail(resized_dimensions, Image.ANTIALIAS)
        self.pil_small_colour_image.crop((0, 0, self.screen_size[0], self.screen_size[1]))

        self.pygame_colour_image = pil_image_to_surface(self.pil_small_colour_image)
        self.framerate = framerate
        self.selection_line_width = selection_line_width
        self.selection_line_colour = selection_line_colour
        print("Finished loading.")

    def get_image_window(self, left, top, mode="colour"):
        if mode=="colour":
            path = str(Path(__name__).absolute().parent.parent.joinpath("tasmania", "colour.tif"))
        else:
            path = str(Path(__name__).absolute().parent.parent.joinpath("tasmania", "heights.tif"))

        with rio.open(path) as rio_src:
            w = rio.windows.Window(left, top, self.screen_size[0], self.screen_size[1])
            if mode=="colour":
                loaded_data = np.zeros((self.screen_size[1], self.screen_size[0], 3), "uint8")
                loaded_data[..., 0] = rio_src.read(1, window=w)
                loaded_data[..., 1] = rio_src.read(2, window=w)
                loaded_data[..., 2] = rio_src.read(3, window=w)
                im = Image.fromarray(loaded_data)
            else:
                loaded_data = rio_src.read(1, window=w)
                if mode=="numpy":
                    return loaded_data
                loaded_data = loaded_data - loaded_data.min()
                loaded_data = loaded_data // (loaded_data.max()/255)
                im = Image.fromarray(loaded_data).convert('RGB')
        return pil_image_to_surface(im)

@dataclass
class VisState:
    running: bool = True
    within_transition: bool = True
    resized_image_position: Tuple[int, int] = (0, 0)
    rectangle_bounds: Tuple = None
    scaled_location: Tuple = None
