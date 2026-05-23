import pygame
from interfaces.i_scene import IScene
from core.data_manager import DataManager
from core.game_stats import game_stats
from core.network_manager import NetworkManager
from core.host_manager import HostManager
from ui.text import UIText
from ui.button import UIButton
from ui.panel import UIPanel


class OverScene(IScene):

    def __init__(self, scene_manager):
        self.scene_manager = scene_manager
        self.ui_elements = []
        self.panel = None
        self.over_text = None
        self.score_text = None
        self.high_score_text = None
        self.rank_texts = []
        self.restart_btn = None
        self.back_btn = None
        self.lobby_btn = None
        self._nm = NetworkManager()

    def init(self):
        dm = DataManager()
        dm.load_save()
        dm.update_high_score(game_stats.score)
        high_score = dm.save_data["high_score"]

        is_multi = self._nm.connected

        panel_height = 360 if is_multi else 320
        self.panel = UIPanel(pygame.Rect(440, 50, 400, panel_height))
        self.over_text = UIText("gameover")
        self.over_text.set_text("游戏结束")

        self.score_text = UIText("score")
        self.score_text.set_text(f"本次得分: {game_stats.score}")
        self.score_text.set_position((640, 220))

        self.high_score_text = UIText("score")
        self.high_score_text.set_text(f"最高分: {high_score}")
        self.high_score_text.set_position((640, 260))

        self.restart_btn = UIButton("restart", callback=self.restart_game)
        self.restart_btn.rect.center = (640, 310)

        if is_multi:
            self.back_btn = UIButton("back_to_lobby", callback=self.back_to_lobby)
            self.back_btn.rect.center = (640, 370)
            self.ui_elements = [self.panel, self.over_text, self.score_text,
                               self.high_score_text, self.restart_btn, self.back_btn]
        else:
            self.back_btn = UIButton("back", callback=self.back_to_main)
            self.back_btn.rect.center = (640, 370)
            self.ui_elements = [self.panel, self.over_text, self.score_text,
                               self.high_score_text, self.restart_btn, self.back_btn]

        self.rank_texts = []

    def restart_game(self):
        self._nm.stop()
        self.scene_manager.reset_scene("game")
        self.scene_manager.switch_scene("game")

    def back_to_main(self):
        self._nm.stop()
        self.scene_manager.reset_scene("game")
        self.scene_manager.reset_scene("start")
        self.scene_manager.switch_scene("start")

    def back_to_lobby(self):
        self._nm.stop()
        self.scene_manager.reset_scene("game")
        self.scene_manager.reset_scene("lobby")
        self.scene_manager.switch_scene("lobby")

    def handle_event(self, event: pygame.event.Event):
        for elem in self.ui_elements:
            if hasattr(elem, "handle_event"):
                elem.handle_event(event)
        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            self.back_to_main()

    def update(self):
        for elem in self.ui_elements:
            elem.update()

        while not self._nm.recv_queue.empty():
            try:
                msg = self._nm.recv_queue.get_nowait()
                if msg["type"] == 8:
                    scores = msg.get("data", {}).get("scores", {})
                    self._show_multi_ranking(scores)
            except Exception:
                pass

    def _show_multi_ranking(self, scores: dict):
        self.rank_texts = []
        sorted_scores = sorted(scores.items(), key=lambda x: x[1], reverse=True)
        y = 280
        for i, (pid, sc) in enumerate(sorted_scores[:3]):
            rank_text = UIText("score")
            rank_text.set_text(f"第{i + 1}名: {pid} - {sc}分")
            rank_text.set_position((640, y))
            self.rank_texts.append(rank_text)
            y += 30
        self.ui_elements = [self.panel, self.over_text, self.score_text,
                           self.high_score_text] + self.rank_texts + [self.restart_btn, self.back_btn]

    def draw(self, screen: pygame.Surface):
        screen.fill((0, 0, 0))
        for elem in self.ui_elements:
            elem.draw(screen)
        pygame.display.flip()
