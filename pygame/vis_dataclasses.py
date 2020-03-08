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
    image = Image.fromarray(numpy.uint8(cm.viridis(height_map / height_map.max()) * 255))
    return pygame.image.fromstring(image.tobytes(), image.size, image.mode)


def crop(image: pygame.Surface, size) -> pygame.Surface:
    image_size = image.get_rect().size
    scale_ratio = max(size[0]/image_size[0], size[1]/image_size[1])
    return pygame.transform.scale(image, [int(dimension * scale_ratio) for dimension in image_size])


class VisSettings:
    def __init__(
        self,
        screen_size: Tuple[int, int],
        framerate: int = 165,
    ):
        self.screen_size = screen_size
        self.height_map = load_heights()
        self.screen_size_height_image = crop(height_map_to_image(self.height_map), self.screen_size)
        self.screen_size_true_colour = crop(load_true_colour(), self.screen_size)
        self.framerate = framerate


@dataclass
class VisState:
    running: bool = True
    within_transition: bool = True
