import pygame
from interfaces.i_scene import IScene
from core.data_manager import DataManager
from core.game_stats import game_stats
from ui.text import UIText
from ui.button import UIButton
from ui.panel import UIPanel


class OverScene(IScene):
    """结束界面：显示本次得分、最高分、重新开始和退出按钮"""

    def __init__(self, scene_manager):
        self.scene_manager = scene_manager
        self.ui_elements = []
        self.panel = None
        self.over_text = None
        self.score_text = None
        self.high_score_text = None
        self.restart_btn = None
        self.back_btn = None

    def init(self):
        """初始化结束界面：获取分数并创建UI元素"""
        dm = DataManager()
        dm.load_save()
        dm.update_high_score(game_stats.score)  # 使用 game_stats 获取分数
        high_score = dm.save_data["high_score"]

        self.panel = UIPanel(pygame.Rect(120, 100, 400, 320))
        self.over_text = UIText("gameover")
        self.over_text.set_text("游戏结束")

        self.score_text = UIText("score")
        self.score_text.set_text(f"本次得分: {game_stats.score}")  # 使用 game_stats
        self.score_text.set_position((320, 220))

        self.high_score_text = UIText("score")
        self.high_score_text.set_text(f"最高分: {high_score}")
        self.high_score_text.set_position((320, 260))

        # 重新开始按钮
        self.restart_btn = UIButton("restart", callback=self.restart_game)
        self.restart_btn.rect.center = (320, 300)
        
        # 返回主界面按钮（放在重新开始按钮下面）
        self.back_btn = UIButton("back", callback=self.back_to_main)
        self.back_btn.rect.center = (320, 370)
        self.ui_elements = [self.panel, self.over_text, self.score_text, self.high_score_text, self.restart_btn, self.back_btn]

    def restart_game(self):
        """重新开始游戏：重置游戏场景并切换"""
        self.scene_manager.reset_scene("game")
        self.scene_manager.switch_scene("game")

    def back_to_main(self):
        """返回主界面：重置游戏场景和开始场景，确保最高分被重新加载"""
        self.scene_manager.reset_scene("game")
        self.scene_manager.reset_scene("start")  # 重置开始场景以重新加载最高分
        self.scene_manager.switch_scene("start")

    def handle_event(self, event: pygame.event.Event):
        """处理输入事件"""
        for elem in self.ui_elements:
            if hasattr(elem, "handle_event"):
                elem.handle_event(event)
        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            self.back_to_main()

    def update(self):
        """更新UI元素"""
        for elem in self.ui_elements:
            elem.update()

    def draw(self, screen: pygame.Surface):
        """绘制界面"""
        screen.fill((0, 0, 0))
        for elem in self.ui_elements:
            elem.draw(screen)
        pygame.display.flip()