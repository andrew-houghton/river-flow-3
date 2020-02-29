import pygame
from pathlib import Path
from PIL import Image


def get_image(filename):
    image = Image.open(Path(__file__).absolute().parent.parent.joinpath("data", filename))
    return pygame.image.fromstring(image.tobytes(), image.size, image.mode)

pygame.init()
infoObject = pygame.display.Info()
size = (infoObject.current_w, infoObject.current_h)

screen = pygame.display.set_mode(size)
pygame.display.set_mode(size, pygame.FULLSCREEN)

clock = pygame.time.Clock()

# Set startup state
true_colour = get_image("true_colour_resized.jpg")
ballrect = true_colour.get_rect()
screen.blit(true_colour, ballrect)
pygame.display.flip()

running = True
while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                running = False  # Set running to False to end the while loop.
            elif event.key == pygame.K_LEFT:
                pass
            elif event.key == pygame.K_RIGHT:
                pass

    clock.tick(165)
