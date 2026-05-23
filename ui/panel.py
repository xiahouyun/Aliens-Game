import pygame
from interfaces.i_ui_component import IUIComponent
from core.data_manager import DataManager


class UIPanel(IUIComponent):
    """面板组件：弹窗背景，半透明矩形"""

    def __init__(self, rect: pygame.Rect, config_name="game.json"):
        self.dm = DataManager()
        self.dm.load_config(config_name)
        self.rect = rect
        self.color = self.dm.get_config(config_name, "ui.panel_color")
        self.surface = pygame.Surface(self.rect.size, pygame.SRCALPHA)
        self.surface.fill(self.color)

    def update(self):
        """面板无需更新"""
        pass

    def draw(self, screen: pygame.Surface):
        """绘制面板"""
        screen.blit(self.surface, self.rect.topleft)