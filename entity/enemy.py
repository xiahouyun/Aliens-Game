import pygame
import random
from interfaces.i_entity import IEntity
from core.constants import SCREENRECT
from core.physics_system import PhysicsSystem

# 物理系统单例
physics_system = PhysicsSystem()


class Alien(pygame.sprite.Sprite, IEntity):
    """外星人：左右移动，碰到边界反弹"""

    images = []         # 外星人图片列表
    containers = None   # 所属精灵组

    def __init__(self):
        pygame.sprite.Sprite.__init__(self, self.containers)
        self.image = self.images[0]
        self.rect = self.image.get_rect()
        config = physics_system.get_entity_config("alien")
        self.facing = physics_system.create_facing_vector(config["speed"])
        self.frame = 0
        if self.facing.x < 0:
            self.rect.right = SCREENRECT.right
        self.health = 100  # 外星人血量（0-100）
        self.max_health = 100

    def update(self):
        """移动外星人（调用物理系统）"""
        physics_system.move_alien(self)

    def take_damage(self, damage):
        """受到伤害"""
        self.health = max(0, self.health - damage)

    def draw(self, screen):
        """外星人无需手动绘制（由精灵组绘制）"""
        pass