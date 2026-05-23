import pygame


class CollisionSystem:
    """碰撞检测系统：统一管理所有碰撞检测逻辑"""

    @staticmethod
    def check_player_alien_collision(player, aliens):
        """玩家与外星人碰撞"""
        return pygame.sprite.spritecollide(player, aliens, True)

    @staticmethod
    def check_shot_alien_collision(aliens, shots):
        """子弹与外星人碰撞"""
        return pygame.sprite.groupcollide(aliens, shots, False, True)

    @staticmethod
    def check_player_bomb_collision(player, bombs):
        """玩家与炸弹碰撞"""
        return pygame.sprite.spritecollide(player, bombs, True)