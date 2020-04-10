from vis_dataclasses import VisState, VisSettings
from typing import Generator
from random import randint
import pygame
from matplotlib import cm


def starting_image(screen, state: VisState, settings: VisSettings) -> Generator:
    screen.blit(settings.screen_size_true_colour, (0, 0))
    yield


def true_colour_to_height_map(screen, state: VisState, settings: VisSettings) -> Generator:
    num_steps = 50
    fading_out_image = settings.screen_size_true_colour.copy()

    for i in range(num_steps, 0, -1):
        image_alpha = int(255 * i / num_steps)
        fading_out_image.set_alpha(image_alpha)
        screen.blit(settings.screen_size_height_image, (0, 0))
        screen.blit(fading_out_image, (0, 0))
        yield

    screen.blit(settings.screen_size_height_image, (0, 0))
    yield


def compute_selection_pixel_size(screen_size, max_pixels):
    # Wide dimension of the screen is max_pixels
    # Other dimension of the screen is the same scale
    pixel_size = max(screen_size) / max_pixels
    return int(screen_size[0] / pixel_size), int(screen_size[1] / pixel_size)


def display_selection_polygon(screen, state: VisState, settings: VisSettings) -> Generator:
    # TODO: Only show polygon within screen

    state.selection_pixel_size = compute_selection_pixel_size(settings.screen_size, settings.max_pixels)

    shown_screen_dimensions = [int(i / settings.scale_ratio) for i in settings.screen_size]
    left = randint(0, shown_screen_dimensions[0] - 1 - state.selection_pixel_size[0])
    right = left + state.selection_pixel_size[0]
    top = randint(0, shown_screen_dimensions[1] - 1 - state.selection_pixel_size[1])
    bottom = top + state.selection_pixel_size[1]

    state.points = ((left, top), (right, top), (right, bottom), (left, bottom))
    state.scaled_points = [(int(x * settings.scale_ratio), int(y * settings.scale_ratio)) for x, y in state.points]
    pygame.draw.polygon(
        settings.screen_size_height_image,
        settings.selection_line_colour,
        state.scaled_points,
        settings.selection_line_width,
    )
    screen.blit(settings.screen_size_height_image, (0, 0))
    yield


def scale_up_selection(screen, state: VisState, settings: VisSettings) -> Generator:
    # Get the section of the image
    # Scale up the section step by step
    selected_surface = settings.full_size_height_image.subsurface(
        pygame.Rect(
            state.points[0][0],
            state.points[0][1],
            state.points[2][0] - state.points[0][0],
            state.points[2][1] - state.points[0][1],
        )
    )

    num_steps = 200

    for i in range(num_steps + 1):
        # Smoothly transition the scale of the selected surface to cover the whole screen
        # TODO: change this section so that it looks like a flat surface moving closer to an observer
        proportion_finished = (i / num_steps) ** 3
        proportion_unfinished = 1 - proportion_finished

        width = int(
            state.selection_pixel_size[0] * settings.scale_ratio * proportion_unfinished
            + settings.screen_size[0] * proportion_finished
        )
        height = int(
            state.selection_pixel_size[1] * settings.scale_ratio * proportion_unfinished
            + settings.screen_size[1] * proportion_finished
        )

        left = int(state.scaled_points[0][0] * proportion_unfinished)
        top = int(state.scaled_points[0][1] * proportion_unfinished)

        state.resized_selected_surface = pygame.transform.scale(selected_surface, (width, height))
        screen.blit(state.resized_selected_surface, (left, top))
        yield



def add_circles(screen, state: VisState, settings: VisSettings) -> Generator:

    def draw_circles(screen_size, height_array, surface, dimensions):
        float_pixel_size = (screen_size[0] / dimensions[0], screen_size[1] / dimensions[1])
        center_offset = (float_pixel_size[0] / 2, float_pixel_size[1] / 2)
        circle_radius = int(max(*float_pixel_size) * 0.35)
        height_array = (height_array // (height_array.max() / 255)).astype("int32")

        for x in range(dimensions[0]):
            for y in range(dimensions[1]):
                height = height_array[state.points[0][1] + y, state.points[0][0] + x]
                colour = [i * 255 for i in cm.viridis(height / 255)[:3]]
                pygame.draw.circle(
                    surface,
                    colour,
                    (int(x * float_pixel_size[0] + center_offset[0]), int(y * float_pixel_size[1] + center_offset[1])),
                    circle_radius,
                )

    state.circles_surface = pygame.Surface(settings.screen_size, pygame.SRCALPHA, 32).convert_alpha()
    draw_circles(settings.screen_size, settings.height_map, state.circles_surface, state.selection_pixel_size)

    # Remove background image
    num_steps = 200
    state.resized_selected_surface = state.resized_selected_surface.convert()
    for i in range(num_steps, -1, -1):
        image_alpha = int(255 * i / num_steps)
        state.resized_selected_surface.set_alpha(image_alpha)
        screen.fill((0, 0, 0))
        screen.blit(state.resized_selected_surface, (0, 0))
        screen.blit(state.circles_surface, (0, 0))
        yield

def add_edges(screen, state: VisState, settings: VisSettings) -> Generator:

    float_pixel_size = (
        settings.screen_size[0] / state.selection_pixel_size[0],
        settings.screen_size[1] / state.selection_pixel_size[1],
    )
    center_offset = (float_pixel_size[0] / 2, float_pixel_size[1] / 2)
    screen.fill((0, 0, 0))
    for i in range(sum(state.selection_pixel_size)):
        for j in range(i):
            # Horizontal lines
            if i-j < state.selection_pixel_size[0]:
                pygame.draw.line(
                    screen,
                    (255, 255, 255),
                    (
                        int((i-j-1) * float_pixel_size[0] + center_offset[0]),
                        int(j * float_pixel_size[1] + center_offset[1]),
                    ),
                    (
                        int((i-j) * float_pixel_size[0] + center_offset[0]),
                        int(j * float_pixel_size[1] + center_offset[1]),
                    ),
                    2,
                )
            # Vertical lines
            if i-j < state.selection_pixel_size[1]:
                pygame.draw.line(
                    screen,
                    (255, 255, 255),
                    (
                        int(j * float_pixel_size[0] + center_offset[0]),
                        int((i-j-1) * float_pixel_size[1] + center_offset[1]),
                    ),
                    (
                        int(j * float_pixel_size[0] + center_offset[0]),
                        int((i-j) * float_pixel_size[1] + center_offset[1]),
                    ),
                    2,
                )
        screen.blit(state.circles_surface, (0, 0))
        yield
