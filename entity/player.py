import pygame
from interfaces.i_entity import IEntity
from core.constants import SCREENRECT
from core.physics_system import PhysicsSystem

# 物理系统单例
physics_system = PhysicsSystem()


class Player(pygame.sprite.Sprite, IEntity):
    """玩家飞船"""

    images = []         # 玩家图片列表
    containers = None   # 所属精灵组

    def __init__(self, spawn_pos=None):
        super().__init__(self.containers)
        self.image = self.images[0]
        if spawn_pos:
            self.rect = self.image.get_rect(midbottom=spawn_pos)
        else:
            self.rect = self.image.get_rect(midbottom=SCREENRECT.midbottom)
        self.reloading = False
        self.origtop = self.rect.top
        self.facing = -1
        self.health = 100
        self.max_health = 100

    def move(self, direction):
        """移动玩家（调用物理系统）"""
        physics_system.move_player(self, direction)

    def gunpos(self):
        """获取子弹发射位置（调用物理系统）"""
        return physics_system.get_gunpos(self)

    def take_damage(self, damage):
        """受到伤害"""
        self.health = max(0, self.health - damage)

    def update(self):
        """玩家无需每帧更新"""
        pass

    def draw(self, screen):
        """玩家无需手动绘制（由精灵组绘制）"""
        pass