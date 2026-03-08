# -*- coding: utf-8 -*-
"""
通用工具函数模块

该模块提供了项目中通用的工具函数，包括：
- API Key 遮罩处理
- 会话目录路径获取
- 配置文件读写操作

使用方式:
    from app.utils.helpers import mask_api_key, read_config_file
"""
import json
from pathlib import Path
from typing import Optional, Tuple


def mask_api_key(key: str) -> str:
    """
    遮罩 API Key，只显示前4位和后4位

    用于日志输出或 API 响应中隐藏敏感信息。

    参数:
        key: 原始 API Key

    返回:
        str: 遮罩后的 API Key 字符串

    示例:
        >>> mask_api_key("sk-1234567890abcdef")
        "sk-1...cdef"
    """
    if not key or len(key) <= 8:
        return "****"
    return f"{key[:4]}...{key[-4:]}"


def get_sessions_dir(workspace_path: str) -> Path:
    """
    获取会话存储目录路径

    参数:
        workspace_path: 工作区根路径

    返回:
        Path: 会话目录的完整路径

    示例:
        >>> get_sessions_dir("/home/user/.nanobot/workspace")
        Path("/home/user/.nanobot/workspace/sessions")
    """
    return Path(workspace_path) / "sessions"


def get_config_path() -> Path:
    """
    获取 Nanobot 配置文件路径

    返回:
        Path: config.json 文件的完整路径

    示例:
        >>> get_config_path()
        Path("/home/user/.nanobot/config.json")
    """
    return Path.home() / ".nanobot" / "config.json"


def read_config_file() -> Tuple[Optional[dict], Optional[str]]:
    """
    读取 Nanobot 配置文件

    从 ~/.nanobot/config.json 读取配置内容。

    返回:
        Tuple[Optional[dict], Optional[str]]:
            - 第一个元素：配置字典（成功时）或 None（失败时）
            - 第二个元素：错误信息（失败时）或 None（成功时）

    示例:
        >>> config, error = read_config_file()
        >>> if error:
        ...     print(f"读取失败: {error}")
        ... else:
        ...     print(f"配置: {config}")
    """
    config_path = get_config_path()

    if not config_path.exists():
        return None, "配置文件不存在"

    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            return json.load(f), None
    except json.JSONDecodeError as e:
        return None, f"JSON 格式错误: {e}"
    except Exception as e:
        return None, str(e)


def write_config_file(config_data: dict) -> Tuple[bool, Optional[str]]:
    """
    写入 Nanobot 配置文件（原子操作）

    使用临时文件实现原子写入，确保配置文件不会因为写入中断而损坏。

    参数:
        config_data: 要写入的配置字典

    返回:
        Tuple[bool, Optional[str]]:
            - 第一个元素：是否成功
            - 第二个元素：错误信息（失败时）或 None（成功时）

    示例:
        >>> success, error = write_config_file({"providers": {...}})
        >>> if not success:
        ...     print(f"写入失败: {error}")
    """
    config_path = get_config_path()

    try:
        # 使用临时文件实现原子写入
        temp_path = config_path.with_suffix(".json.tmp")
        with open(temp_path, 'w', encoding='utf-8') as f:
            json.dump(config_data, f, indent=2, ensure_ascii=False)
        temp_path.rename(config_path)
        return True, None
    except Exception as e:
        return False, str(e)
