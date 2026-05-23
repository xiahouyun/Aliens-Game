import pygame
from interfaces.i_entity import IEntity
from core.physics_system import PhysicsSystem

# 物理系统单例
physics_system = PhysicsSystem()


class Bomb(pygame.sprite.Sprite, IEntity):
    """炸弹：从外星人位置投放，向下移动"""

    images = []         # 炸弹图片列表
    containers = None   # 所属精灵组

    def __init__(self, alien):
        pygame.sprite.Sprite.__init__(self, self.containers)
        self.image = self.images[0]
        self.rect = self.image.get_rect(midbottom=alien.rect.move(0, 5).midbottom)

    def update(self):
        """向下移动（调用物理系统）"""
        physics_system.move_bomb(self)

    def draw(self, screen):
        """炸弹无需手动绘制（由精灵组绘制）"""
        pass