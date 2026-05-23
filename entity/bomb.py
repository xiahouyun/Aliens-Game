import pygame
from interfaces.i_entity import IEntity
from core.physics_system import PhysicsSystem

# 物理系统单例
physics_system = PhysicsSystem()


class Bomb(pygame.sprite.Sprite, IEntity):
    images = []
    containers = None

    def __init__(self, alien):
        pygame.sprite.Sprite.__init__(self, self.containers)
        self.image = self.images[0]
        if alien:
            self.rect = self.image.get_rect(midbottom=alien.rect.move(0, 5).midbottom)
        else:
            self.rect = self.image.get_rect()

    @classmethod
    def from_pos(cls, x, y):
        bomb = cls.__new__(cls)
        pygame.sprite.Sprite.__init__(bomb, cls.containers)
        bomb.image = cls.images[0]
        bomb.rect = bomb.image.get_rect()
        bomb.rect.x = x
        bomb.rect.y = y
        return bomb

    def update(self):
        """向下移动（调用物理系统）"""
        physics_system.move_bomb(self)

    def draw(self, screen):
        """炸弹无需手动绘制（由精灵组绘制）"""
        pass