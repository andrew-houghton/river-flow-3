from dataclasses import dataclass
import pygame
from matplotlib import cm
import numpy
from PIL import Image
from pathlib import Path
from typing import Tuple


def load_heights():
    im = Image.open(Path(__file__).absolute().parent.parent.joinpath("data", "ASTGTMV003_S45E168_dem.tif"))
    return numpy.array(im)


def load_true_colour():
    image = Image.open(Path(__file__).absolute().parent.parent.joinpath("data", "true_colour_resized.jpg"))
    return pygame.image.fromstring(image.tobytes(), image.size, image.mode)


def height_map_to_image(height_map) -> pygame.Surface:
    image = Image.fromarray(numpy.uint8(cm.gist_earth(height_map / height_map.max()) * 255))
    return pygame.image.fromstring(image.tobytes(), image.size, image.mode)


def crop(image: pygame.Surface, scale_ratio: float) -> pygame.Surface:
    return pygame.transform.scale(image, [int(dimension * scale_ratio) for dimension in image.get_rect().size])


class VisSettings:
    def __init__(
        self,
        screen_size: Tuple[int, int],
        framerate: int = 165,
        max_pixels: int = 50,
        selection_line_width: int = 3,
        selection_line_colour: Tuple[int, int, int] = (0, 204, 51),
    ):
        self.screen_size = screen_size
        self.height_map = load_heights()
        self.scale_ratio = max(
            screen_dimension / original_dimension
            for screen_dimension, original_dimension in zip(self.screen_size, self.height_map.shape)
        )
        self.full_size_height_image = height_map_to_image(self.height_map)
        self.screen_size_height_image = crop(height_map_to_image(self.height_map), self.scale_ratio)
        self.screen_size_true_colour = crop(load_true_colour(), self.scale_ratio)
        self.framerate = framerate
        self.max_pixels = max_pixels
        self.selection_line_width = selection_line_width
        self.selection_line_colour = selection_line_colour


@dataclass
class VisState:
    running: bool = True
    within_transition: bool = True
    selection_pixel_size: Tuple[int, int] = None
