import pygame
from interfaces.i_entity import IEntity
from core.physics_system import PhysicsSystem

# 物理系统单例
physics_system = PhysicsSystem()


class Shot(pygame.sprite.Sprite, IEntity):
    """子弹：从玩家位置发射，向上移动"""

    images = []         # 子弹图片列表
    containers = None   # 所属精灵组

    def __init__(self, pos):
        pygame.sprite.Sprite.__init__(self, self.containers)
        self.image = self.images[0]
        self.rect = self.image.get_rect(midbottom=pos)

    def update(self):
        """向上移动（调用物理系统）"""
        physics_system.move_shot(self)

    def draw(self, screen):
        """子弹无需手动绘制（由精灵组绘制）"""
        pass