from abc import ABC, abstractmethod
import pygame


class IScene(ABC):
    """场景接口：所有场景必须实现的方法"""

    @abstractmethod
    def init(self):
        """初始化场景"""
        pass

    @abstractmethod
    def handle_event(self, event: pygame.event.Event):
        """处理事件"""
        pass

    @abstractmethod
    def update(self):
        """更新场景逻辑"""
        pass

    @abstractmethod
    def draw(self, screen):
        """绘制场景"""
        pass