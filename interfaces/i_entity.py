from abc import ABC, abstractmethod


class IEntity(ABC):
    """游戏实体接口：玩家、敌人、子弹、爆炸、炸弹"""

    @abstractmethod
    def update(self):
        """更新实体状态"""
        pass

    @abstractmethod
    def draw(self, screen):
        """绘制实体"""
        pass