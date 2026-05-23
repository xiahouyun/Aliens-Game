"""事件总线：用于模块间解耦通信（单例模式）"""
from typing import Callable, Dict, List


class EventBus:
    """事件总线：发布-订阅模式的事件系统"""

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
            self._listeners: Dict[str, List[Callable]] = {}

    def subscribe(self, event_type: str, callback: Callable):
        """订阅事件

        Args:
            event_type: 事件类型，如 "score_changed"
            callback: 回调函数，接收事件数据作为参数
        """
        if event_type not in self._listeners:
            self._listeners[event_type] = []
        if callback not in self._listeners[event_type]:
            self._listeners[event_type].append(callback)

    def unsubscribe(self, event_type: str, callback: Callable):
        """取消订阅

        Args:
            event_type: 事件类型
            callback: 回调函数
        """
        if event_type in self._listeners:
            if callback in self._listeners[event_type]:
                self._listeners[event_type].remove(callback)

    def publish(self, event_type: str, data=None):
        """发布事件

        Args:
            event_type: 事件类型
            data: 事件数据
        """
        if event_type in self._listeners:
            for callback in self._listeners[event_type]:
                callback(data)

    def clear(self, event_type: str = None):
        """清空事件监听

        Args:
            event_type: 如果为None，清空所有；否则只清空指定类型
        """
        if event_type is None:
            self._listeners.clear()
        elif event_type in self._listeners:
            self._listeners[event_type].clear()


# 预定义事件类型常量
class EventTypes:
    """事件类型常量"""
    SCORE_CHANGED = "score_changed"
    PLAYER_DIED = "player_died"
    GAME_OVER = "game_over"
    SCENE_CHANGED = "scene_changed"
    MULTIPLAYER_PLAYER_JOINED = "multiplayer_player_joined"
    MULTIPLAYER_PLAYER_LEFT = "multiplayer_player_left"
    MULTIPLAYER_STATE_CHANGED = "multiplayer_state_changed"


# 全局事件总线单例
event_bus = EventBus()