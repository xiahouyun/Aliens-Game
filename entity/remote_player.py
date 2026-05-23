import pygame
from interfaces.i_entity import IEntity


class RemotePlayer(pygame.sprite.Sprite, IEntity):
    images = []
    containers = None

    def __init__(self, player_id: str, x: float = 0, y: float = 0):
        pygame.sprite.Sprite.__init__(self, self.containers)
        self.player_id = player_id
        if self.images:
            self.image = self.images[0]
        else:
            self.image = pygame.Surface((32, 32))
            self.image.fill((0, 255, 0))
        self.rect = self.image.get_rect()
        self.rect.x = x
        self.rect.y = y
        self.health = 100
        self.max_health = 100
        self.facing = -1
        self.score = 0
        self.shooting = False
        self.reloading = False
        self.origtop = self.rect.top

    def move(self, direction, speed):
        if direction:
            self.facing = direction
        self.rect.move_ip(direction * speed, 0)
        from core.constants import SCREENRECT
        self.rect = self.rect.clamp(SCREENRECT)
        if self.images:
            self.image = self.images[0] if self.facing < 0 else self.images[1]
        self.origtop = self.rect.top

    def update_from_state(self, state: dict):
        self.rect.x = state.get("x", self.rect.x)
        self.rect.y = state.get("y", self.rect.y)
        self.health = state.get("health", self.health)
        self.facing = state.get("facing", self.facing)
        self.score = state.get("score", self.score)
        self.shooting = state.get("shooting", self.shooting)
        if self.images:
            self.image = self.images[0] if self.facing < 0 else self.images[1]

    def update(self):
        pass

    def draw(self, screen):
        pass
