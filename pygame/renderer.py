# Controls the flow through the program
# Responsible for managing control flow and data flow, and rendering frames
# Defines which animations will run, and the order they run in

import os
os.environ["PYGAME_HIDE_SUPPORT_PROMPT"] = "hide"
import pygame
import animations
import flow_animations
import actions
import flow_actions
import vis_dataclasses
import flow_dataclasses

class VisRenderer:
    def __init__(self):
        pygame.init()
        infoObject = pygame.display.Info()
        self.current_animation_index = -1

        fullscreen_mode = True
        animation = "algorithm"

        if animation == "algorithm":
            dataclass_module = vis_dataclasses
            self.animations = [
                (animations.starting_image, None, "New Zealand", None),
                (animations.true_colour_to_height_map, actions.show_selection_polygon, "Height map", "Click two corners to select an area"),
                (animations.random_selection_polygon, None, "Height map", None),
                (animations.scale_up_selection, None, "Selected area of height map", None),
                (animations.add_circles, None, "Height as points", "Each circle represents a physical point, colour indicates height"),
                (animations.add_edges, None, "Point graph", "Water can flow between points, this flow is represented by lines"),
                (animations.merge_equal_height_nodes, None, "Merge equal height points", "If multiple points next to each other are the same height they are merged"),
                (animations.highlight_low_nodes, None, "Low points", "Points below all adjacent points will flood if water is added"),
                (animations.flood_points, None, "Flooding", "Flood these points until there is a direction for water to flow out and down"),
                (animations.show_only_true_colour, actions.animate_watershed, "Animation: Watershed", "Click somewhere"),
                (animations.show_only_heights, actions.animate_flow, "Animation: Flow", "Click somewhere"),
            ]
        else:
            dataclass_module = flow_dataclasses
            self.animations = [
                (flow_animations.starting_image, flow_actions.show_selection_polygon, "Tasmania", "Click area of interest"),
                (flow_animations.show_selection, None, "Selected area", None),
                (flow_animations.show_selection_height, None, "Selected area height", None),
                (flow_animations.graph_construction_progress, None, "Graph construction", None),
                # (flow_animations.node_merging_progress, None, "Equal height node merging", None),
                # (flow_animations.flooding, None, "Equal height node merging", None),
                # (flow_animations.watershed, None, "Watershed", None),
            ]

        if fullscreen_mode:
            self.settings = dataclass_module.VisSettings(screen_size=(infoObject.current_w, infoObject.current_h))
            self.render_surface = pygame.display.set_mode(self.settings.screen_size, pygame.FULLSCREEN)
        else:
            self.settings = dataclass_module.VisSettings(screen_size=(infoObject.current_w // 2, infoObject.current_h // 2))
            self.render_surface = pygame.display.set_mode(self.settings.screen_size)

        self.state = dataclass_module.VisState(running=True, within_transition=True)
        self.screen = self.render_surface.copy()
        self.clock = pygame.time.Clock()

        pygame.font.init()
        self.title_font = pygame.font.SysFont('tahoma', 48)
        self.subtitle_font = pygame.font.SysFont('tahoma', 32)
        self.title_text = None
        self.subtitle_text = None
        self.main_loop()

    def main_loop(self):
        frame_generator, action_processor = self.next_animation()
        while self.state.running:
            if self.state.within_transition:
                try:
                    next(frame_generator)
                    self.render_surface.blit(self.screen, (0, 0))
                    self.render_surface.blit(self.text_surface, (0, 0))
                    pygame.display.flip()
                    self.clock.tick(self.settings.framerate)
                    self.handle_events()
                except StopIteration:
                    self.state.within_transition = False
            else:
                frame_generator, action_processor = self.handle_events(action_processor)
                if frame_generator:
                    self.state.within_transition = True

    def update_text(self):
        title_string = self.animations[self.current_animation_index][2] 
        subtitle_string = self.animations[self.current_animation_index][3]
        self.title_text = self.title_font.render(title_string, True, (255, 255, 255))
        if subtitle_string is not None:
            self.subtitle_text = self.subtitle_font.render(subtitle_string, True, (255, 255, 255))
        else:
            self.subtitle_text = None

        self.text_surface = pygame.Surface(self.settings.screen_size, pygame.SRCALPHA, 32)
        self.text_surface = self.text_surface.convert_alpha()
        self.text_surface.blit(self.title_text, (0,0))
        if self.subtitle_text:
            self.text_surface.blit(self.subtitle_text, (0,60))

    def next_animation(self):
        self.current_animation_index += 1
        self.update_text()
        generator = self.animations[self.current_animation_index][0](self.screen, self.state, self.settings)
        return generator, self.animations[self.current_animation_index][1]

    def previous_animation(self):
        if self.current_animation_index == 0:
            return None, None
        self.current_animation_index -= 1
        self.update_text()
        generator = self.animations[self.current_animation_index][0](self.screen, self.state, self.settings)
        return generator, self.animations[self.current_animation_index][1]

    def handle_events(self, action_processor=None):
        for event in pygame.event.get():
            if event.type == pygame.QUIT or (event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE):
                self.state.running = False
            elif event.type == pygame.KEYDOWN and event.key == pygame.K_RIGHT and not self.state.within_transition:
                if self.current_animation_index == len(self.animations) - 1:
                    return None, action_processor
                return self.next_animation()
            elif event.type == pygame.KEYDOWN and event.key == pygame.K_LEFT and not self.state.within_transition:
                if self.current_animation_index == 0:
                    return None, action_processor
                return self.previous_animation()
            elif action_processor is not None:
                return action_processor(event, self.screen, self.state, self.settings), action_processor
        return None, action_processor

if __name__ == "__main__":
    VisRenderer()
