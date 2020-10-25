import pygame
import random


def starting_image(screen, state, settings):
    image_size = settings.pygame_colour_image.get_rect().size
    state.resized_image_position = (
        (settings.screen_size[0] - image_size[0]) // 2,
        (settings.screen_size[1] - image_size[1]) // 2,
    )
    screen.fill((0,0,0))
    screen.blit(settings.pygame_colour_image, state.resized_image_position)
    if state.rectangle_bounds:
        pygame.draw.polygon(
            screen,
            settings.selection_line_colour,
            state.rectangle_bounds,
            settings.selection_line_width,
        )
    yield

def show_selection(screen, state, settings):
    if not state.scaled_location:
        state.scaled_location = (
            random.randint(0, settings.full_size_dimensions[0] - settings.screen_size[0] - 1),
            random.randint(0, settings.full_size_dimensions[1] - settings.screen_size[1] - 1),
        )
    state.selected_image = settings.get_image_window(state.scaled_location[0], state.scaled_location[1])
    screen.blit(state.selected_image, (0, 0))
    yield

def show_selection_height(screen, state, settings):
    state.selected_height = settings.get_image_window(state.scaled_location[0], state.scaled_location[1], mode="height")
    screen.blit(state.selected_height, (0, 0))
    yield
