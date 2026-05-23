"""游戏常量配置 - 从game.json加载并提供统一访问"""
import pygame
from core.data_manager import DataManager

# 数据管理器单例
_dm = DataManager()
_dm.load_config("game.json")

# 窗口配置
_WINDOW = _dm.get_config("game.json", "window")
SCREENRECT = pygame.Rect(0, 0, _WINDOW["width"], _WINDOW["height"])
FPS = _WINDOW["fps"]
WINDOW_CAPTION = _WINDOW["caption"]

# 游戏配置
_GAME = _dm.get_config("game.json", "game")
MAX_SHOTS = _GAME["max_shots"]
ALIEN_ODDS = _GAME["alien_odds"]
BOMB_ODDS = _GAME["bomb_odds"]
ALIEN_RELOAD = _GAME["alien_reload"]

# 全局游戏状态
SCORE = 0

# 模块清理，隐藏内部变量
del _dm, _WINDOW, _GAME