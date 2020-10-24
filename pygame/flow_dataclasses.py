from vis_dataclasses import load_image_file_zipped
from pathlib import Path
from typing import Tuple
from dataclasses import dataclass
from PIL import Image
import pygame


def pilImageToSurface(im):
    return pygame.image.fromstring(im.tobytes(), im.size, im.mode)


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
        self.scale_ratio = min(
            screen_dimension / original_dimension
            for screen_dimension, original_dimension in zip(reversed(self.screen_size), self.pil_colour_image.size)
        )
        resized_dimensions = (self.scale_ratio * self.pil_colour_image.size[0], self.scale_ratio* self.pil_colour_image.size[1])
        print("Resizing image")
        self.pil_colour_image.thumbnail(resized_dimensions, Image.ANTIALIAS)
        print("Cropping image")
        self.pil_colour_image.crop((0, 0, self.screen_size[0], self.screen_size[1]))

        self.pygame_colour_image = pilImageToSurface(self.pil_colour_image)
        self.framerate = framerate
        self.selection_line_width = selection_line_width
        self.selection_line_colour = selection_line_colour
        print("Finished loading.")

@dataclass
class VisState:
    running: bool = True
    within_transition: bool = True
    resized_image_position: Tuple[int, int] = (0, 0)
