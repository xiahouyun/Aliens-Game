"""事件监听器接口：定义事件处理的标准方法"""
from abc import ABC, abstractmethod


class IEventListener(ABC):
    """事件监听器接口：所有需要处理事件的类都应实现此接口"""

    @abstractmethod
    def on_event(self, event_type: str, data=None):
        """处理事件的统一方法

        Args:
            event_type: 事件类型，如 "score_changed"
            data: 事件数据，可选参数
        """
        pass

    def subscribe_to_events(self, event_bus):
        """订阅事件（默认实现：订阅所有预定义事件）

        Args:
            event_bus: 事件总线实例
        """
        from core.event_bus import EventTypes
        for event_type in EventTypes.__dict__.values():
            if isinstance(event_type, str):
                event_bus.subscribe(event_type, self.on_event)