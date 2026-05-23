import pygame
from interfaces.i_scene import IScene
from ui.text import UIText
from ui.button import UIButton
from ui.panel import UIPanel


class PauseScene(IScene):
    """暂停界面：显示暂停面板、继续和退出按钮"""

    def __init__(self, scene_manager):
        self.scene_manager = scene_manager
        self.ui_elements = []
        self.panel = None
        self.pause_text = None
        self.resume_btn = None
        self.back_btn = None

    def init(self):
        """初始化：创建UI元素"""
        self.panel = UIPanel(pygame.Rect(170, 150, 300, 300))
        self.pause_text = UIText("pause")
        self.pause_text.set_text("游戏暂停")
        self.resume_btn = UIButton("resume", callback=self.resume_game)
        self.back_btn = UIButton("back", callback=self.back_to_main)
        self.ui_elements = [self.panel, self.pause_text, self.resume_btn, self.back_btn]

    def resume_game(self):
        """继续游戏：切换回游戏场景"""
        self.scene_manager.switch_scene("game")

    def back_to_main(self):
        """返回主界面：重置游戏场景并切换到开始场景"""
        self.scene_manager.reset_scene("game")
        self.scene_manager.switch_scene("start")

    def handle_event(self, event: pygame.event.Event):
        """处理UI元素事件"""
        for elem in self.ui_elements:
            if hasattr(elem, "handle_event"):
                elem.handle_event(event)

        # ESC继续游戏
        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            self.resume_game()

    def update(self):
        """更新UI元素状态"""
        for elem in self.ui_elements:
            elem.update()

    def draw(self, screen: pygame.Surface):
        """绘制界面（保留游戏背景）"""
        for elem in self.ui_elements:
            elem.draw(screen)
        pygame.display.flip()