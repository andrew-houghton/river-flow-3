
def starting_image(screen, state, settings):
    image_size = settings.pygame_colour_image.get_rect().size
    state.resized_image_position = (
        (settings.screen_size[0] - image_size[0]) // 2,
        (settings.screen_size[1] - image_size[1]) // 2,
    )
    screen.blit(settings.pygame_colour_image, state.resized_image_position)
    yield
