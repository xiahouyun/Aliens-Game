import pygame
from interfaces.i_scene import IScene
from core.game_stats import game_stats
from ui.text import UIText
from ui.button import UIButton


class StartScene(IScene):
    """开始界面：显示标题、最高分、开始按钮"""

    def __init__(self, scene_manager):
        self.scene_manager = scene_manager
        self.ui_elements = []  # 所有UI元素的列表
        self.title_text = None
        self.start_btn = None
        self.quit_btn = None
        self.high_score_text = None

    def init(self):
        """初始化：加载最高分、创建UI元素"""
        # 刷新最高分（从保存文件重新读取）
        game_stats.refresh_high_score()
        high_score = game_stats.high_score

        self.title_text = UIText("title")
        self.title_text.set_text("外星人入侵")

        self.high_score_text = UIText("score")
        self.high_score_text.set_text(f"最高分: {high_score}")
        self.high_score_text.rect.center = (320, 150)

        self.start_btn = UIButton("start", callback=self.start_game)
        self.quit_btn = UIButton("quit", callback=self.quit_game)
        self.ui_elements = [self.title_text, self.high_score_text, self.start_btn, self.quit_btn]

    def start_game(self):
        """开始游戏：切换到游戏场景"""
        self.scene_manager.switch_scene("game")

    def quit_game(self):
        """退出游戏：设置退出标志"""
        self.scene_manager.should_quit = True

    def handle_event(self, event: pygame.event.Event):
        """处理UI元素事件"""
        for elem in self.ui_elements:
            if hasattr(elem, "handle_event"):
                elem.handle_event(event)

        # ESC退出游戏
        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            self.scene_manager.should_quit = True

    def update(self):
        """更新UI元素状态"""
        for elem in self.ui_elements:
            elem.update()

    def draw(self, screen: pygame.Surface):
        """绘制界面"""
        screen.fill((0, 0, 0))
        for elem in self.ui_elements:
            elem.draw(screen)
        pygame.display.flip()