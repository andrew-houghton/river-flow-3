from abc import ABC, abstractmethod
from .vis_dataclasses import VisState, VisSettings


class Animation(ABC):
    @abstractmethod
    def __init__(self, screen, state: VisState, settings: VisSettings) -> Generator:
        pass


class StartingImage(Animation):
    def __init__(self, screen, state: VisState, settings: VisSettings) -> Generator:
        screen.blit(settings.true_colour, (0, 0))
        yield


class TrueColourToHeightMap(Animation):
    def __init__(self, screen, state: VisState, settings: VisSettings) -> Generator:
        num_steps = 200
        fading_out_image = settings.true_colour.copy()

        for image_alpha in range(255, 0, -255 / num_steps):
            fading_out_image.set_alpha(image_alpha)
            screen.blit(settings.height_map, (0, 0))
            screen.blit(fading_out_image, (0, 0))
            yield

        screen.blit(settings.height_map, (0, 0))
        yield
