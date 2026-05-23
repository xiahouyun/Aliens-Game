"""场景管理器：管理所有场景的注册、切换、重置"""


class SceneManager:
    """场景管理器：管理所有场景的注册、切换、重置"""

    def __init__(self):
        self.scenes = {}              # 已注册的场景字典
        self.current_scene = None     # 当前场景
        self.scene_initialized = {}   # 记录场景是否已初始化
        self.should_quit = False      # 退出标志

    def register_scene(self, name: str, scene):
        """注册场景"""
        self.scenes[name] = scene
        self.scene_initialized[name] = False

    def switch_scene(self, name: str):
        """切换场景（首次切换时会初始化）"""
        if name in self.scenes:
            self.current_scene = self.scenes[name]
            if not self.scene_initialized[name]:
                self.current_scene.init()
                self.scene_initialized[name] = True

    def reset_scene(self, name: str):
        """重置场景状态，下次进入时会重新初始化"""
        if name in self.scene_initialized:
            self.scene_initialized[name] = False

    def handle_event(self, event):
        """将事件分发给当前场景"""
        if self.current_scene:
            self.current_scene.handle_event(event)

    def update(self):
        """更新当前场景"""
        if self.current_scene:
            self.current_scene.update()

    def draw(self, screen):
        """绘制当前场景"""
        if self.current_scene:
            self.current_scene.draw(screen)