import pygame
from interfaces.i_ui_component import IUIComponent
import core.constants as const
from core.data_manager import DataManager


class UIText(IUIComponent):
    def __init__(self, key: str, config_name="ui.json"):
        self.dm = DataManager()
        self.dm.load_config(config_name)
        self.cfg = self.dm.get_config(config_name, f"text.{key}")
        self.font_path = self.dm.get_config("game.json", "ui.font_path")
        self.size = self.cfg.get("size", self.dm.get_config("game.json", "ui.font_size"))
        self.color = self.cfg["color"]
        self.pos = self.cfg["pos"]
        self.text = ""
        self.font = pygame.font.Font(self.font_path, self.size)
        self.image = None
        self.rect = None
        self._use_custom_pos = False  # 标记是否使用自定义位置
        self.update()

    def set_text(self, text: str):
        self.text = text
        self.update()
    
    def set_position(self, pos):
        """手动设置位置"""
        self.pos = pos
        self._use_custom_pos = True
        if self.rect:
            self.rect.center = pos

    def update(self):
        self.image = self.font.render(self.text, True, self.color)
        # 如果使用自定义位置，保持当前位置；否则使用配置位置
        if self._use_custom_pos and self.rect:
            self.rect = self.image.get_rect(center=self.rect.center)
        else:
            self.rect = self.image.get_rect(center=self.pos)

    def draw(self, screen: pygame.Surface):
        if self.image:
            screen.blit(self.image, self.rect)
