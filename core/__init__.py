"""初始化游戏核心模块，确保配置正确加载"""
from core.data_manager import DataManager

# 全局数据管理器单例
data_manager = DataManager()

def init():
    """初始化游戏核心"""
    global data_manager
    if not data_manager.configs:
        data_manager.load_config("game.json")
        data_manager.load_config("ui.json")
        data_manager.load_save()
    return data_manager