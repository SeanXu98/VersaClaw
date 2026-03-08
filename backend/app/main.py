# -*- coding: utf-8 -*-
"""
FastAPI 应用工厂模块

该模块负责创建和配置 FastAPI 应用，包括：
- 应用生命周期管理（启动、关闭）
- CORS 中间件配置
- 路由注册
- 根路径和健康检查端点

使用方式:
    from app.main import app

    # 或在入口点
    import uvicorn
    from app.main import app
    uvicorn.run(app, host="0.0.0.0", port=18790)
"""
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.services.nanobot_service import NanobotService
from app.dependencies import set_nanobot_service
from app.routers import (
    chat_router,
    sessions_router,
    images_router,
    models_router,
    config_router
)

# 配置日志
logger = logging.getLogger(__name__)

# 全局 Nanobot 服务实例
nanobot_service = NanobotService()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    应用生命周期管理器

    在应用启动时：
    - 初始化 Nanobot 服务
    - 设置依赖注入

    在应用关闭时：
    - 清理 Nanobot 服务资源
    """
    # ==================== 启动阶段 ====================
    logger.info("[应用] 🚀 正在启动 Nanobot API Server...")
    await nanobot_service.initialize()
    set_nanobot_service(nanobot_service)

    yield

    # ==================== 关闭阶段 ====================
    await nanobot_service.shutdown()
    logger.info("[应用] 👋 Nanobot API Server 已关闭")


def create_app() -> FastAPI:
    """
    创建并配置 FastAPI 应用

    该函数负责：
    1. 创建 FastAPI 实例
    2. 配置 CORS 中间件
    3. 注册所有路由
    4. 添加根路径和健康检查端点

    返回:
        FastAPI: 配置完成的 FastAPI 应用实例
    """
    app = FastAPI(
        title="Nanobot API Server",
        version="0.1.0",
        lifespan=lifespan
    )

    # ==================== CORS 中间件配置 ====================
    # 允许所有来源访问（生产环境应限制具体域名）
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # ==================== 注册路由 ====================
    app.include_router(chat_router)
    app.include_router(sessions_router)
    app.include_router(images_router)
    app.include_router(models_router)
    app.include_router(config_router)

    # ==================== 根路径端点 ====================
    @app.get("/", tags=["基础"])
    async def root():
        """
        根路径端点

        返回 API 服务的基本信息。
        """
        return {
            "name": "Nanobot API Server",
            "version": "0.1.0",
            "status": "running"
        }

    # ==================== 健康检查端点 ====================
    @app.get("/health", tags=["基础"])
    async def health():
        """
        健康检查端点

        用于检查服务是否正常运行，以及 Nanobot 是否已初始化。
        """
        return {
            "status": "healthy",
            "nanobot_initialized": nanobot_service.is_initialized
        }

    return app


# 创建应用实例
app = create_app()
