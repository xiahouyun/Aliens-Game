import pygame
from core.constants import SCREENRECT


class PhysicsSystem:
    """物理移动系统：负责所有实体的移动和边界检测"""

    _instance = None
    _initialized = False

    def __new__(cls):
        """单例模式"""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        """延迟初始化"""
        if not self._initialized:
            self._initialized = True
            # 延迟导入，避免循环导入
            from core.data_manager import DataManager
            self.dm = DataManager()
            self.dm.load_config("game.json")
            # 从配置获取物理参数
            self.ENTITY_CONFIG = {
                "player": {
                    "speed": self.dm.get_config("game.json", "entity.player.speed"),
                    "bounce": self.dm.get_config("game.json", "entity.player.bounce"),
                    "gun_offset": self.dm.get_config("game.json", "entity.player.gun_offset"),
                },
                "alien": {
                    "speed": self.dm.get_config("game.json", "entity.alien.speed"),
                    "animcycle": self.dm.get_config("game.json", "entity.alien.animcycle"),
                },
                "shot": {
                    "speed": self.dm.get_config("game.json", "entity.shot.speed"),
                },
                "bomb": {
                    "speed": self.dm.get_config("game.json", "entity.bomb.speed"),
                },
                "explosion": {
                    "defaultlife": self.dm.get_config("game.json", "entity.explosion.defaultlife"),
                    "animcycle": self.dm.get_config("game.json", "entity.explosion.animcycle"),
                },
            }

    def move_player(self, player, direction):
        """移动玩家飞船

        Args:
            player: 玩家对象
            direction: 方向 (-1左, 1右, 0不动)
        """
        config = self.ENTITY_CONFIG["player"]
        if direction:
            player.facing = direction
        player.rect.move_ip(direction * config["speed"], 0)
        player.rect = player.rect.clamp(SCREENRECT)
        if direction < 0:
            player.image = player.images[0]
        elif direction > 0:
            player.image = player.images[1]
        player.rect.top = player.origtop - (player.rect.left // config["bounce"] % 2)

    def get_gunpos(self, player):
        """获取子弹发射位置"""
        config = self.ENTITY_CONFIG["player"]
        pos = player.facing * config["gun_offset"] + player.rect.centerx
        return pos, player.rect.top

    def move_alien(self, alien):
        """移动外星人

        Args:
            alien: 外星人对象
        """
        config = self.ENTITY_CONFIG["alien"]
        alien.rect.move_ip(alien.facing.x, 0)
        if not SCREENRECT.contains(alien.rect):
            alien.facing.x = -alien.facing.x
            alien.rect.top = alien.rect.bottom + 1
            alien.rect = alien.rect.clamp(SCREENRECT)
        alien.frame += 1
        alien.image = alien.images[alien.frame // config["animcycle"] % 3]

    def move_shot(self, shot):
        """移动子弹

        Args:
            shot: 子弹对象
        """
        config = self.ENTITY_CONFIG["shot"]
        shot.rect.move_ip(0, config["speed"])
        if shot.rect.top <= 0:
            shot.kill()

    def move_bomb(self, bomb):
        """移动炸弹

        Args:
            bomb: 炸弹对象
        """
        config = self.ENTITY_CONFIG["bomb"]
        bomb.rect.move_ip(0, config["speed"])
        if bomb.rect.bottom >= 470:
            # 使用延迟导入避免循环导入
            try:
                from entity.explosion import Explosion
                Explosion(bomb)
            except ImportError:
                pass
            bomb.kill()

    def update_explosion(self, explosion):
        """更新爆炸动画

        Args:
            explosion: 爆炸对象
        """
        config = self.ENTITY_CONFIG["explosion"]
        explosion.life -= 1
        explosion.image = explosion.images[explosion.life // config["animcycle"] % 2]
        if explosion.life <= 0:
            explosion.kill()

    def get_entity_config(self, entity_type):
        """获取实体配置

        Args:
            entity_type: 实体类型

        Returns:
            配置字典
        """
        return self.ENTITY_CONFIG[entity_type]

    def create_facing_vector(self, speed, flip_chance=0.5):
        """创建移动向量

        Args:
            speed: 速度
            flip_chance: 随机翻转概率

        Returns:
            移动向量
        """
        import random
        return pygame.math.Vector2(random.choice((-1, 1)) * speed, 0)