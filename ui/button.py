import pygame
from interfaces.i_ui_component import IUIComponent
from core.data_manager import DataManager


class UIButton(pygame.sprite.Sprite, IUIComponent):
    """按钮组件：支持悬停效果和点击回调"""

    def __init__(self, key: str, callback=None, config_name="ui.json"):
        super().__init__()
        self.dm = DataManager()
        self.dm.load_config(config_name)
        self.cfg = self.dm.get_config(config_name, f"button.{key}")
        self.callback = callback  # 点击回调函数

        self.pos = self.cfg["pos"]
        self.size = self.cfg["size"]
        self.text = self.cfg["text"]
        self.rect = pygame.Rect(
            self.pos[0] - self.size[0] // 2,
            self.pos[1] - self.size[1] // 2,
            *self.size
        )
        self.image = pygame.Surface((self.size[0], self.size[1]), pygame.SRCALPHA)
        self.image.fill((0, 0, 0, 0))

        # 颜色配置
        self.color = self.dm.get_config("game.json", "ui.button_color")
        self.hover_color = self.dm.get_config("game.json", "ui.button_hover_color")

        # 字体配置
        self.font_path = self.dm.get_config("game.json", "ui.font_path")
        self.font_size = self.dm.get_config("game.json", "ui.font_size")
        self.font = pygame.font.Font(self.font_path, self.font_size)

        self.text_color = (255, 255, 255)
        self.text_surf = self.font.render(self.text, True, self.text_color)
        self.text_rect = self.text_surf.get_rect(center=self.rect.center)

    def handle_event(self, event: pygame.event.Event):
        """处理鼠标点击事件"""
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.rect.collidepoint(event.pos):
                if self.callback:
                    self.callback()

    def update(self):
        """更新（按钮无需每帧更新）"""
        pass

    def draw(self, screen: pygame.Surface):
        """绘制按钮：支持悬停变色"""
        mouse_pos = pygame.mouse.get_pos()
        current_color = self.hover_color if self.rect.collidepoint(mouse_pos) else self.color
        pygame.draw.rect(screen, current_color, self.rect, border_radius=8)
        # 动态计算文本位置，确保与按钮中心对齐
        self.text_rect = self.text_surf.get_rect(center=self.rect.center)
        screen.blit(self.text_surf, self.text_rect)