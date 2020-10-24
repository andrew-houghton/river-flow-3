import pygame

def show_selection_polygon(event, screen, state, settings):
    if event.type == pygame.MOUSEBUTTONDOWN:
        state.click_location = pygame.mouse.get_pos()
        scaled_location = (
            int(state.click_location[0] / settings.scale_ratio),
            int(state.click_location[1] / settings.scale_ratio),
        )
        print(scaled_location)

    # screen.blit(settings.screen_size_true_colour, (0, 0))
    # pygame.draw.polygon(
    #     screen,
    #     settings.selection_line_colour,
    #     state.scaled_points,
    #     settings.selection_line_width,
    # )
    # screen.blit(settings.screen_size_height_image, (0, 0))
    yield
