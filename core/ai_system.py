import random
from core.constants import ALIEN_ODDS, ALIEN_RELOAD, BOMB_ODDS


class AISystem:
    """AI系统：控制外星人生成和炸弹投放"""

    @staticmethod
    def need_spawn_alien(timer):
        """判断是否需要生成外星人"""
        if timer <= 0 and not int(random.random() * ALIEN_ODDS):
            return True
        return False

    @staticmethod
    def reset_alien_timer():
        """重置外星人生成计时器"""
        return ALIEN_RELOAD

    @staticmethod
    def need_drop_bomb():
        """判断是否需要投放炸弹"""
        return not int(random.random() * BOMB_ODDS)