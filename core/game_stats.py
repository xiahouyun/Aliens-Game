"""游戏状态管理器：管理分数、最高分等游戏状态（单例模式）"""
import core.constants as const
from core.event_bus import event_bus, EventTypes
from core.data_manager import DataManager


class GameStats:
    """游戏状态管理器：管理分数、最高分等游戏状态"""

    _instance = None
    _initialized = False

    def __new__(cls):
        """单例模式"""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        """延迟初始化"""
        if not self._initialized:
            self._initialized = True
            self._score = 0
            # 从保存文件中加载最高分
            dm = DataManager()
            dm.load_save()
            self._high_score = dm.save_data.get("high_score", 0)

    def reset(self):
        """重置游戏状态（重新开始时调用）"""
        self._score = 0
        event_bus.publish(EventTypes.SCORE_CHANGED, {"score": 0})

    def add_score(self, points: int):
        """加分

        Args:
            points: 要增加的分数
        """
        self._score += points
        event_bus.publish(EventTypes.SCORE_CHANGED, {"score": self._score})

    @property
    def score(self):
        """获取当前分数"""
        return self._score

    @score.setter
    def score(self, value: int):
        """设置分数（直接设置，不发布事件）"""
        self._score = value
        event_bus.publish(EventTypes.SCORE_CHANGED, {"score": self._score})

    @property
    def high_score(self):
        """获取最高分"""
        return self._high_score

    def set_high_score(self, value: int):
        """设置最高分"""
        if value > self._high_score:
            self._high_score = value
            event_bus.publish(EventTypes.SCORE_CHANGED, {"high_score": self._high_score})

    def refresh_high_score(self):
        """从保存文件刷新最高分（用于场景切换时更新显示）"""
        dm = DataManager()
        dm.load_save()
        self._high_score = dm.save_data.get("high_score", 0)


# 全局游戏状态单例
game_stats = GameStats()