import pygame
from interfaces.i_ui_component import IUIComponent
from core.data_manager import DataManager


class UIPlayerList(IUIComponent):
    def __init__(self, x: int, y: int, config_name="game.json"):
        self.dm = DataManager()
        self.dm.load_config(config_name)
        self.x = x
        self.y = y
        self.font_path = self.dm.get_config(config_name, "ui.font_path")
        self.font_size = self.dm.get_config(config_name, "ui.font_size")
        self.font = pygame.font.Font(self.font_path, self.font_size)
        self.small_font = pygame.font.Font(self.font_path, 18)
        self.text_color = (255, 255, 255)
        self.ready_color = (0, 255, 0)
        self.wait_color = (255, 255, 0)
        self.players = {}
        self.rect = pygame.Rect(x, y, 300, 200)

    def set_players(self, players: dict):
        self.players = players

    def add_player(self, player_id: str, ready: bool = False):
        self.players[player_id] = ready

    def remove_player(self, player_id: str):
        if player_id in self.players:
            del self.players[player_id]

    def update(self):
        pass

    def draw(self, screen: pygame.Surface):
        y_offset = self.y
        title = self.small_font.render("玩家列表", True, self.text_color)
        screen.blit(title, (self.x, y_offset))
        y_offset += 25
        for pid, ready in self.players.items():
            status = "就绪" if ready else "等待"
            color = self.ready_color if ready else self.wait_color
            text = f"  {pid}  [{status}]"
            surf = self.font.render(text, True, color)
            screen.blit(surf, (self.x, y_offset))
            y_offset += 28
