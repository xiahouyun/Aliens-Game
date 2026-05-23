import pygame
from interfaces.i_scene import IScene
from core.game_stats import game_stats
from ui.text import UIText
from ui.button import UIButton


class StartScene(IScene):

    def __init__(self, scene_manager):
        self.scene_manager = scene_manager
        self.ui_elements = []
        self.title_text = None
        self.start_btn = None
        self.multiplayer_btn = None
        self.quit_btn = None
        self.high_score_text = None

    def init(self):
        game_stats.refresh_high_score()
        high_score = game_stats.high_score

        self.title_text = UIText("title")
        self.title_text.set_text("外星人入侵")

        self.high_score_text = UIText("score")
        self.high_score_text.set_text(f"最高分: {high_score}")
        self.high_score_text.rect.center = (640, 150)

        self.start_btn = UIButton("start", callback=self.start_game)
        self.multiplayer_btn = UIButton("multiplayer", callback=self.go_multiplayer)
        self.quit_btn = UIButton("quit", callback=self.quit_game)
        self.ui_elements = [self.title_text, self.high_score_text, self.start_btn,
                           self.multiplayer_btn, self.quit_btn]

    def start_game(self):
        self.scene_manager.switch_scene("game")

    def go_multiplayer(self):
        self.scene_manager.reset_scene("lobby")
        self.scene_manager.switch_scene("lobby")

    def quit_game(self):
        self.scene_manager.should_quit = True

    def handle_event(self, event: pygame.event.Event):
        for elem in self.ui_elements:
            if hasattr(elem, "handle_event"):
                elem.handle_event(event)

        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            self.scene_manager.should_quit = True

    def update(self):
        for elem in self.ui_elements:
            elem.update()

    def draw(self, screen: pygame.Surface):
        screen.fill((0, 0, 0))
        for elem in self.ui_elements:
            elem.draw(screen)
        pygame.display.flip()
