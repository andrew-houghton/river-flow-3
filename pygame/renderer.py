import pygame
from .vis_dataclasses import VisState, VisSettings
from itertools import chain
from .animations import StartingImage, TrueColourToHeightMap


class VisRenderer:
    def __init__(self):
        pygame.init()
        self.settings = VisSettings(screen_size=pygame.display.Info())
        self.state = VisState(running=True, within_transition=True)

        self.screen = pygame.display.set_mode(self.settings.screen_size, pygame.FULLSCREEN)
        self.clock = pygame.time.Clock()

        self.animations = [
            StartingImage(screen, self.state, self.settings),
            TrueColourToHeightMap(screen, self.state, self.settings),
        ]
        self.main_loop()

    def main_loop(self):
        frame_generator = next_animation()
        while self.state.running:
            if self.state.within_transition:
                try:
                    frame_generator.next()
                    pygame.display.flip()
                    self.clock.tick(self.framerate)
                    self.handle_events()
                except StopIteration:
                    self.state.within_transition = False
            else:
                frame_generator = self.handle_events()
                if frame_generator:
                    self.state.within_transition = True

    def next_animation(self):
        try:
            return self.animations.pop(0)
        except IndexError:
            return

    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT or (event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE):
                self.state.running = False
            elif event.type == pygame.KEYDOWN and event.key == pygame.K_RIGHT and not self.state.within_transition:
                return self.next_animation(self.screen)


if __name__ == "__main__":
    VisRenderer()
