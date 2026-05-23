from abc import ABC, abstractmethod
import pygame


class IUIComponent(ABC):
    """UI组件接口：文字、按钮、面板、进度条"""

    @abstractmethod
    def update(self):
        """更新组件状态"""
        pass

    @abstractmethod
    def draw(self, screen: pygame.Surface):
        """绘制组件"""
        pass