import json
import os
from typing import Dict, Any


class DataManager:
    """数据管理器：加载配置文件和存档"""

    def __init__(self, config_dir="configs", data_dir="data"):
        self.config_dir = config_dir
        self.data_dir = data_dir
        self.configs: Dict[str, Any] = {}
        self.save_data: Dict[str, Any] = {"high_score": 0}

    def load_config(self, filename: str) -> Dict[str, Any]:
        """加载配置文件"""
        path = os.path.join(self.config_dir, filename)
        with open(path, "r", encoding="utf-8") as f:
            self.configs[filename] = json.load(f)
        return self.configs[filename]

    def get_config(self, filename: str, key_path: str):
        """按路径读取配置，如 "game.json:ui.font_size" """
        cfg = self.configs.get(filename)
        if not cfg:
            cfg = self.load_config(filename)
        keys = key_path.split(".")
        value = cfg
        for k in keys:
            value = value[k]
        return value

    def load_save(self, filename="save.json"):
        """加载存档"""
        path = os.path.join(self.data_dir, filename)
        if not os.path.exists(path):
            self.save_data = {"high_score": 0}
            self.save_save(filename)
        else:
            with open(path, "r", encoding="utf-8") as f:
                self.save_data = json.load(f)
        return self.save_data

    def save_save(self, filename="save.json"):
        """保存存档"""
        path = os.path.join(self.data_dir, filename)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(self.save_data, f, indent=4)

    def update_high_score(self, score: int):
        """更新最高分"""
        if score > self.save_data.get("high_score", 0):
            self.save_data["high_score"] = score
            self.save_save()