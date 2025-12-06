"""
插件配置管理
"""

import json
import os
from typing import Any


class UserConfig:
    """用户配置管理类，用于存储和管理每个用户的独立配置"""

    def __init__(self, config_dir: str):
        """初始化用户配置管理器

        Args:
            config_dir: 配置文件目录
        """
        self.config_dir = config_dir
        os.makedirs(self.config_dir, exist_ok=True)
        self.user_configs: dict[str, dict[str, Any]] = {}

    def get_user_config(
        self, user_id: str, default_config: dict[str, Any]
    ) -> dict[str, Any]:
        """获取用户配置，如果不存在则使用默认配置

        Args:
            user_id: 用户ID
            default_config: 默认配置

        Returns:
            用户配置
        """
        if user_id not in self.user_configs:
            # 尝试从文件加载用户配置
            config_path = os.path.join(self.config_dir, f"user_{user_id}.json")
            user_config = default_config.copy()

            if os.path.exists(config_path):
                try:
                    with open(config_path, encoding="utf-8") as f:
                        loaded_config = json.load(f)
                        user_config.update(loaded_config)
                except Exception as e:
                    import logging

                    logging.error(f"加载用户配置失败：{str(e)}")

            self.user_configs[user_id] = user_config

        return self.user_configs[user_id]

    def save_user_config(self, user_id: str, config: dict[str, Any]) -> None:
        """保存用户配置到文件

        Args:
            user_id: 用户ID
            config: 用户配置
        """
        # 更新内存中的配置
        self.user_configs[user_id] = config.copy()

        # 保存到文件
        config_path = os.path.join(self.config_dir, f"user_{user_id}.json")
        try:
            with open(config_path, "w", encoding="utf-8") as f:
                json.dump(config, f, ensure_ascii=False, indent=2)
        except Exception as e:
            import logging

            logging.error(f"保存用户配置失败：{str(e)}")

    def update_user_config(
        self, user_id: str, updates: dict[str, Any], default_config: dict[str, Any]
    ) -> dict[str, Any]:
        """更新用户配置

        Args:
            user_id: 用户ID
            updates: 要更新的配置项
            default_config: 默认配置

        Returns:
            更新后的用户配置
        """
        # 获取当前用户配置
        user_config = self.get_user_config(user_id, default_config)

        # 更新配置
        user_config.update(updates)

        # 保存到文件
        self.save_user_config(user_id, user_config)

        return user_config


class Config:
    """插件配置类"""

    def __init__(self, config: dict[str, Any] = None):
        # 默认配置
        self.default_config = {
            "api_domain": "api.copymanga.site",
            "custom_api_domain": "",
            "api_domain_mode": "Default",
            "download_dir": os.path.join(os.path.dirname(__file__), "downloads"),
            "export_dir": os.path.join(os.path.dirname(__file__), "exports"),
            "token": "",
            "search_limit": 20,  # 搜索结果最大返回数量
            "chapter_content_mode": "single",  # 章节内容返回方式，merge表示合并转发整章内容，single表示单页发送
            "search_display_limit": 10,  # 一次合并转发消息最多显示的漫画数量
        }

        # 从传入的配置中加载，或使用默认配置
        merged_config = {**self.default_config, **(config or {})}

        self.config = merged_config

        # 加载命令配置
        self._load_command_config()

        # 初始化用户配置管理器
        config_dir = os.path.join(os.path.dirname(__file__), "user_configs")
        self.user_config_manager = UserConfig(config_dir)

    def _load_command_config(self):
        """加载命令配置"""
        # 命令列表
        command_list = [
            "copymanga_login",
            "copymanga_search",
            "copymanga_select_comic",
            "copymanga_select_chapter",
            "copymanga_chapter_mode",
            "copymanga_profile",
            "copymanga_config",
            "copymanga_test_api",
            "copymanga_next",
            "copymanga_prev",
            "copymanga_jump",
            "copymanga_next_page",
            "copymanga_prev_page",
            "copymanga_help",
        ]

        # 初始化命令配置
        self.commands = {}
        self.command_names = {}

        # 加载命令配置
        for command_name in command_list:
            config_key = f"command_{command_name}"
            command_config = self.config.get(config_key, {})

            # 提取启用状态和命令名称
            enabled = command_config.get("enabled", True)
            custom_command_name = command_config.get("command_name", command_name)

            # 保存命令配置
            self.commands[command_name] = enabled
            self.command_names[command_name] = custom_command_name

    def get_config(self) -> dict[str, Any]:
        """获取当前配置"""
        return self.config.copy()

    def set_config(self, config: dict[str, Any]) -> None:
        """设置配置"""
        self.config.update(config)
        # 重新加载命令配置
        self._load_command_config()

    def get_api_domain(self) -> str:
        """获取API域名"""
        if (
            self.config["api_domain_mode"] == "Custom"
            and self.config["custom_api_domain"]
        ):
            return self.config["custom_api_domain"]
        return self.config["api_domain"]

    def get_authorization(self) -> str:
        """获取授权头"""
        return f"Token {self.config['token']}" if self.config["token"] else ""

    def get_download_dir(self) -> str:
        """获取下载目录"""
        return self.config["download_dir"]

    def get_export_dir(self) -> str:
        """获取导出目录"""
        return self.config["export_dir"]

    def get_user_chapter_content_mode(self, user_id: str) -> str:
        """获取用户的章节内容模式

        Args:
            user_id: 用户ID

        Returns:
            章节内容模式
        """
        user_config = self.user_config_manager.get_user_config(user_id, self.config)
        return user_config.get(
            "chapter_content_mode", self.config["chapter_content_mode"]
        )

    def set_user_chapter_content_mode(self, user_id: str, mode: str) -> None:
        """设置用户的章节内容模式

        Args:
            user_id: 用户ID
            mode: 章节内容模式
        """
        self.user_config_manager.update_user_config(
            user_id, {"chapter_content_mode": mode}, self.config
        )
