import pygame
from pathlib import Path
from PIL import Image


class GameState:
    def __init__(self):
        pygame.init()
        infoObject = pygame.display.Info()
        size = (infoObject.current_w, infoObject.current_h)
        print(f"Creating fullscreen window {size}")
        self.screen = pygame.display.set_mode(size, pygame.FULLSCREEN)

        self.clock = pygame.time.Clock()

        # Set startup state
        true_colour = self.get_image("true_colour_resized.jpg")
        ballrect = true_colour.get_rect()
        self.screen.blit(true_colour, ballrect)
        pygame.display.flip()

        self.running = True

    @staticmethod
    def get_image(filename):
        image = Image.open(Path(__file__).absolute().parent.parent.joinpath("data", filename))
        return pygame.image.fromstring(image.tobytes(), image.size, image.mode)

    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    self.running = False
                elif event.key == pygame.K_LEFT:
                    pass
                elif event.key == pygame.K_RIGHT:
                    pass

    def main_loop(self):
        pygame.display.update()
        while self.running:
            self.handle_events()
            self.clock.tick(165)

if __name__ == "__main__":
    game = GameState()
    game.main_loop()
