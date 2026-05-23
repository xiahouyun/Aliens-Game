import pygame
from interfaces.i_entity import IEntity
from core.physics_system import PhysicsSystem

# 物理系统单例
physics_system = PhysicsSystem()


class Explosion(pygame.sprite.Sprite, IEntity):
    """爆炸效果：播放动画后自动销毁"""

    images = []        # 爆炸图片列表
    containers = None  # 所属精灵组

    def __init__(self, actor):
        pygame.sprite.Sprite.__init__(self, self.containers)
        self.image = self.images[0]
        self.rect = self.image.get_rect(center=actor.rect.center)
        config = physics_system.get_entity_config("explosion")
        self.life = config["defaultlife"]

    @classmethod
    def from_pos(cls, x, y):
        exp = cls.__new__(cls)
        pygame.sprite.Sprite.__init__(exp, cls.containers)
        exp.image = cls.images[0]
        exp.rect = exp.image.get_rect(center=(x, y))
        config = physics_system.get_entity_config("explosion")
        exp.life = config["defaultlife"]
        return exp

    def update(self):
        """播放爆炸动画（调用物理系统）"""
        physics_system.update_explosion(self)

    def draw(self, screen):
        """爆炸无需手动绘制（由精灵组绘制）"""
        pass