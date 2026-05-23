# 血条组件
import pygame
from interfaces.i_ui_component import IUIComponent
from core.data_manager import DataManager


class UIProgressBar(IUIComponent):
    def __init__(self, x, y, width=200, height=20, config_name="game.json"):
        self.dm = DataManager()
        self.dm.load_config(config_name)
        self.rect = pygame.Rect(x, y, width, height)
        self.bg_color = self.dm.get_config(config_name, "ui.progress_bar_bg")
        self.fill_color = self.dm.get_config(config_name, "ui.progress_bar_fill")
        self.value = 100  # 0-100

    def set_value(self, value: int):
        self.value = max(0, min(100, value))

    def update(self):
        pass

    def draw(self, screen: pygame.Surface):
        # 背景
        pygame.draw.rect(screen, self.bg_color, self.rect)
        # 填充
        fill_rect = pygame.Rect(self.rect.x, self.rect.y, self.rect.width * self.value / 100, self.rect.height)
        pygame.draw.rect(screen, self.fill_color, fill_rect)
        # 边框
        pygame.draw.rect(screen, (255, 255, 255), self.rect, 1)
