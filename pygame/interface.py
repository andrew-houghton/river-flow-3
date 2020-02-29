import pygame
from pathlib import Path
from PIL import Image


class GameState:
    def __init__(self):
        pygame.init()
        infoObject = pygame.display.Info()
        size = (infoObject.current_w, infoObject.current_h)
        print(f"Creating fullscreen window {size}")
        # self.screen = pygame.display.set_mode(size, pygame.FULLSCREEN)
        self.screen = pygame.display.set_mode(size)
        self.framerate = 165
        self.clock = pygame.time.Clock()

        # Load images
        self.true_colour = self.get_image("true_colour_resized.jpg", size)
        self.height_map = self.get_image("ASTGTMV003_S45E168_dem.png", size)

        # Set startup image
        self.screen.blit(self.true_colour, self.find_centered_image_corner(self.true_colour))
        pygame.display.flip()

        self.running = True
        self.in_transition = False
        self.screen_number = 0

    def find_centered_image_corner(self, image):
        screen_center = self.screen.get_rect().center
        image_position = image.get_rect().center
        return (screen_center[0] - image_position[0], screen_center[1] - image_position[1])

    @staticmethod
    def get_image(filename, size):
        image = Image.open(Path(__file__).absolute().parent.parent.joinpath("data", filename))
        surface = pygame.image.fromstring(image.tobytes(), image.size, image.mode)
        scale_ratio = min(size[0] / image.size[0], size[1] / image.size[1])
        new_size = [int(i * scale_ratio) for i in image.size]
        return pygame.transform.scale(surface, new_size)

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
                    self.next_screen()

    def main_loop(self):
        while self.running:
            self.handle_events()
            self.clock.tick(self.framerate)

    def next_screen(self):
        self.in_transition = True
        self.screen_number += 1
        if self.screen_number == 1:
            fading_out_image = self.true_colour.copy()

            corner = self.find_centered_image_corner(fading_out_image)
            num_steps = 60

            for i in range(num_steps, 0, -1):
                image_alpha = int(255 * i / num_steps)
                fading_out_image.set_alpha(image_alpha)
                self.screen.blit(self.height_map, corner)
                self.screen.blit(fading_out_image, corner)
                pygame.display.flip()
                self.clock.tick(self.framerate)

        self.in_transition = False


if __name__ == "__main__":
    game = GameState()
    game.main_loop()
