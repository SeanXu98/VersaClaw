#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Nanobot API Server 入口文件

这是 Nanobot API 服务器的入口点，负责启动 FastAPI 应用。

项目结构:
    backend/
    ├── api_server.py          # 本文件 - 入口点
    ├── stream_processor.py    # 流式处理模块
    └── app/
        ├── __init__.py        # 应用包初始化
        ├── main.py            # FastAPI 应用工厂
        ├── config.py          # 配置管理
        ├── dependencies.py    # 依赖注入
        ├── models/            # Pydantic 数据模型
        │   ├── __init__.py
        │   └── schemas.py
        ├── routers/           # API 路由处理
        │   ├── __init__.py
        │   ├── chat.py        # 聊天接口
        │   ├── sessions.py    # 会话管理
        │   ├── images.py      # 图片上传
        │   ├── models.py      # Provider 管理
        │   └── config.py      # 配置管理
        ├── services/          # 业务逻辑层
        │   ├── __init__.py
        │   ├── nanobot_service.py
        │   └── image_service.py
        └── utils/             # 工具函数
            ├── __init__.py
            ├── vision.py
            └── helpers.py

使用方式:
    python api_server.py

环境变量:
    NANOBOT_API_HOST: 监听地址，默认 0.0.0.0
    NANOBOT_API_PORT: 监听端口，默认 18790
"""

import sys
import io
import os
import uvicorn

# 设置标准输出编码为 UTF-8（解决 Windows 中文显示问题）
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# 导入 FastAPI 应用
from app.main import app

if __name__ == "__main__":
    # 从环境变量读取配置
    host = os.getenv("NANOBOT_API_HOST", "0.0.0.0")
    port = int(os.getenv("NANOBOT_API_PORT", "18790"))

    # 打印启动信息
    print("=" * 50)
    print("🤖 Nanobot API Server")
    print("=" * 50)
    print(f"📡 服务地址: http://{host}:{port}")
    print(f"📚 API 文档: http://{host}:{port}/docs")
    print(f"🔧 健康检查: http://{host}:{port}/health")
    print("=" * 50)
    print()

    # 启动服务
    uvicorn.run(
        "api_server:app",
        host=host,
        port=port,
        reload=False,
        log_level="info"
    )
