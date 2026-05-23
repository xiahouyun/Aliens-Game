"""资源管理器：统一管理游戏资源的加载和缓存"""
import os
import pygame


class ResourceManager:
    """游戏资源管理器：图片、声音等资源的加载和缓存"""

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
            self._cache = {}  # 资源缓存
            self.main_dir = os.path.split(os.path.abspath(__file__))[0]
            self.root_dir = os.path.dirname(self.main_dir)
            self.assets_dir = os.path.join(self.root_dir, "assets")

    def get_image_path(self, filename):
        """获取图片资源路径"""
        return os.path.join(self.assets_dir, "images", filename)

    def get_sound_path(self, filename):
        """获取声音资源路径"""
        return os.path.join(self.assets_dir, "sounds", filename)

    def load_image(self, file: str, use_cache: bool = True):
        """加载图片资源

        Args:
            file: 图片文件名
            use_cache: 是否使用缓存

        Returns:
            加载好的图片Surface对象
        """
        if use_cache and file in self._cache.get("images", {}):
            return self._cache["images"][file]

        path = self.get_image_path(file)
        try:
            surface = pygame.image.load(path)
            surface = surface.convert()
        except pygame.error:
            raise SystemExit(f'Could not load image "{path}" {pygame.get_error()}')

        if use_cache:
            if "images" not in self._cache:
                self._cache["images"] = {}
            self._cache["images"][file] = surface

        return surface

    def load_sound(self, file: str, use_cache: bool = True):
        """加载声音资源

        Args:
            file: 声音文件名
            use_cache: 是否使用缓存

        Returns:
            加载好的Sound对象，如果没有mixer则返回None
        """
        if not pygame.mixer:
            return None

        if use_cache and file in self._cache.get("sounds", {}):
            return self._cache["sounds"][file]

        path = self.get_sound_path(file)
        try:
            sound = pygame.mixer.Sound(path)
        except pygame.error:
            print(f"Warning, unable to load, {file}")
            return None

        if use_cache:
            if "sounds" not in self._cache:
                self._cache["sounds"] = {}
            self._cache["sounds"][file] = sound

        return sound

    def clear_cache(self):
        """清空资源缓存"""
        self._cache.clear()

    def preload_images(self, files: list):
        """预加载多个图片

        Args:
            files: 图片文件名列表
        """
        for file in files:
            self.load_image(file)

    def preload_sounds(self, files: list):
        """预加载多个声音

        Args:
            files: 声音文件名列表
        """
        for file in files:
            self.load_sound(file)


# 全局资源管理器单例
resource_manager = ResourceManager()