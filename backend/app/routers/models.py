# -*- coding: utf-8 -*-
"""
模型和 Provider 管理 API 路由模块

该模块提供模型和 Provider 管理相关的 API 端点：
- GET /api/models/{model}/capabilities: 获取模型能力信息
- GET /api/models/providers: 获取所有 Provider 列表
- GET /api/models/providers/{name}: 获取单个 Provider 配置
- POST /api/models/providers/{name}: 保存 Provider 配置
- DELETE /api/models/providers/{name}: 删除 Provider 配置

Provider 分类：
- 网关服务：OpenRouter、AIHubMix 等
- 国际服务商：OpenAI、Anthropic、DeepSeek 等
- 国内服务商：智谱、通义千问、Moonshot 等
- 本地部署：vLLM 等
"""
import logging
from fastapi import APIRouter, Depends

from app.services.nanobot_service import NanobotService
from app.dependencies import get_nanobot_service, get_nanobot_service_optional
from app.models.schemas import ProviderConfigRequest, ModelConfigRequest
from app.config import PROVIDER_METADATA
from app.utils.vision import is_vision_model
from app.utils.helpers import read_config_file, write_config_file

# 配置日志
logger = logging.getLogger(__name__)

# 创建路由器
router = APIRouter(prefix="/api/models", tags=["模型管理"])


@router.get("/{model}/capabilities")
async def get_model_capabilities(model: str):
    """
    获取模型能力信息

    返回指定模型的能力信息，包括是否支持视觉理解、工具调用等。

    参数:
        - model: 模型名称

    响应:
        - success: 是否成功
        - data.model: 模型名称
        - data.vision: 是否支持视觉理解
        - data.tools: 是否支持工具调用
    """
    return {
        "success": True,
        "data": {
            "model": model,
            "vision": is_vision_model(model),
            "tools": True  # 大多数现代模型都支持工具调用
        }
    }


@router.get("/providers")
async def list_providers(
    service: NanobotService = Depends(get_nanobot_service_optional)
):
    """
    获取所有 Provider 列表及配置状态

    返回所有支持的 Provider 列表，包括：
    - Provider 元数据（显示名称、关键词、文档链接）
    - 配置状态（是否已配置 API Key）
    - 可用模型列表
    - Vision 模型数量

    响应:
        - success: 是否成功
        - data.all: 所有 Provider 列表
        - data.categorized: 按类别分组的 Provider
        - data.configured: 已配置的 Provider 名称列表
    """
    try:
        # 直接从配置文件读取（因为 config.providers 是对象不是字典）
        config_data, error = read_config_file()
        configured_providers_dict = config_data.get("providers", {}) if config_data else {}

        # 构建 Provider 列表
        providers = []
        for name, meta in PROVIDER_METADATA.items():
            provider_config = configured_providers_dict.get(name, {})
            is_configured = bool(provider_config.get("api_key"))
            configured_models = provider_config.get("models", [])
            vision_models_count = sum(1 for m in (configured_models or []) if is_vision_model(m))

            providers.append({
                "name": name,
                **meta,
                "status": "active" if is_configured else "inactive",
                "configured_models": configured_models,
                "vision_models_count": vision_models_count
            })

        # 按类别分组
        categorized = {
            "gateway": [p for p in providers if p.get("is_gateway")],
            "international": [
                p for p in providers
                if not p.get("is_gateway")
                and not p.get("is_local")
                and "chinese" not in p.get("keywords", [])
            ],
            "chinese": [
                p for p in providers
                if not p.get("is_gateway")
                and not p.get("is_local")
                and "chinese" in p.get("keywords", [])
            ],
            "local": [p for p in providers if p.get("is_local")]
        }

        logger.info(f"[模型管理] 列出 Provider 成功，共 {len(providers)} 个，已配置 {len([p for p in providers if p['status'] == 'active'])} 个")

        return {
            "success": True,
            "data": {
                "all": providers,
                "categorized": categorized,
                "configured": [p["name"] for p in providers if p["status"] == "active"]
            }
        }

    except Exception as e:
        logger.error(f"[模型管理] 列出 Provider 失败: {e}")
        return {"success": False, "error": str(e)}


@router.get("/providers/{provider_name}")
async def get_provider_config(provider_name: str):
    """
    获取单个 Provider 配置

    返回指定 Provider 的配置信息（不含 API Key）。

    参数:
        - provider_name: Provider 名称

    响应:
        - success: 是否成功
        - data.apiBase: API 基础 URL
        - data.models: 可用模型列表
        - data.hasApiKey: 是否已配置 API Key
    """
    try:
        config_data, error = read_config_file()

        if error:
            return {"success": False, "error": error}

        if not config_data:
            return {"success": False, "error": "配置文件不存在"}

        providers_data = config_data.get("providers", {})
        p = providers_data.get(provider_name)

        if not p or not p.get("api_key"):
            return {"success": False, "error": "Provider 未配置"}

        # 返回配置，但隐藏 API Key
        return {
            "success": True,
            "data": {
                "apiBase": p.get("api_base"),
                "models": p.get("models", []),
                "hasApiKey": bool(p.get("api_key"))
            }
        }

    except Exception as e:
        logger.error(f"[模型管理] 获取 Provider 配置失败: {e}")
        return {"success": False, "error": str(e)}


@router.post("/providers/{provider_name}")
async def save_provider_config(
    provider_name: str,
    request: ProviderConfigRequest,
    service: NanobotService = Depends(get_nanobot_service_optional)
):
    """
    保存 Provider 配置

    保存或更新指定 Provider 的配置，包括 API Key、API Base、模型列表等。

    参数:
        - provider_name: Provider 名称

    请求体:
        - api_key: API 密钥（必填）
        - api_base: API 基础 URL（可选）
        - models: 可用模型列表（可选）
        - extra_headers: 额外请求头（可选）

    响应:
        - success: 是否成功
        - data.message: 成功消息
    """
    try:
        # 读取当前配置
        config_data, error = read_config_file()
        if error and "不存在" not in error and "not found" not in error.lower():
            return {"success": False, "error": error}

        config_data = config_data or {}

        # 确保 providers 字段存在
        if "providers" not in config_data:
            config_data["providers"] = {}

        # 更新或添加 Provider 配置
        provider_data = {"api_key": request.api_key}
        if request.api_base:
            provider_data["api_base"] = request.api_base
        if request.models:
            provider_data["models"] = request.models
        if request.extra_headers:
            provider_data["extra_headers"] = request.extra_headers

        config_data["providers"][provider_name] = provider_data

        # 如果配置了模型，设置默认模型
        if request.models and len(request.models) > 0:
            if "agents" not in config_data:
                config_data["agents"] = {}
            if "defaults" not in config_data["agents"]:
                config_data["agents"]["defaults"] = {}
            config_data["agents"]["defaults"]["model"] = request.models[0]

        # 写入配置
        success, error = write_config_file(config_data)
        if not success:
            return {"success": False, "error": error}

        # 如果服务已初始化，重新加载
        if service and service.is_initialized:
            await service.reload()

        logger.info(f"[模型管理] 保存 Provider 配置成功: {provider_name}")
        return {"success": True, "data": {"message": f"Provider {provider_name} 配置成功"}}

    except Exception as e:
        logger.error(f"[模型管理] 保存 Provider 配置失败: {e}")
        import traceback
        traceback.print_exc()
        return {"success": False, "error": str(e)}


@router.delete("/providers/{provider_name}")
async def delete_provider_config(
    provider_name: str,
    service: NanobotService = Depends(get_nanobot_service_optional)
):
    """
    删除 Provider 配置

    删除指定 Provider 的配置。

    参数:
        - provider_name: Provider 名称

    响应:
        - success: 是否成功
        - data.message: 成功消息
    """
    try:
        config_data, error = read_config_file()

        if error:
            return {"success": False, "error": error}

        if not config_data:
            return {"success": False, "error": "配置文件不存在"}

        if "providers" not in config_data or provider_name not in config_data["providers"]:
            return {"success": False, "error": "Provider 未配置"}

        # 删除 Provider
        del config_data["providers"][provider_name]

        # 写入配置
        success, error = write_config_file(config_data)
        if not success:
            return {"success": False, "error": error}

        # 如果服务已初始化，重新加载
        if service and service.is_initialized:
            await service.reload()

        logger.info(f"[模型管理] 删除 Provider 配置成功: {provider_name}")
        return {"success": True, "data": {"message": f"Provider {provider_name} 已移除"}}

    except Exception as e:
        logger.error(f"[模型管理] 删除 Provider 配置失败: {e}")
        return {"success": False, "error": str(e)}


@router.get("/config")
async def get_model_config():
    """
    获取当前模型配置

    返回主模型和视觉模型的配置信息。

    响应:
        - success: 是否成功
        - data.model: 主模型名称
        - data.imageModel: 视觉模型配置
            - primary: 首选视觉模型
            - fallbacks: 备选模型列表
            - autoSwitch: 是否自动切换
        - data.allModels: 所有已配置的模型列表（来自所有 Provider）
        - data.visionModels: 支持视觉能力的模型列表
    """
    try:
        config_data, error = read_config_file()

        if error and "不存在" not in error and "not found" not in error.lower():
            return {"success": False, "error": error}

        config_data = config_data or {}

        # 获取主模型
        agents_config = config_data.get("agents", {})
        defaults = agents_config.get("defaults", {})
        main_model = defaults.get("model")

        # 获取视觉模型配置
        image_model_config = defaults.get("imageModel", {})

        # 收集所有已配置的模型
        all_models = []
        providers_config = config_data.get("providers", {})
        for provider_name, provider_config in providers_config.items():
            if provider_config.get("api_key"):
                models = provider_config.get("models", [])
                all_models.extend(models)

        # 去重
        all_models = list(dict.fromkeys(all_models))

        # 识别视觉模型
        vision_models = [m for m in all_models if is_vision_model(m)]

        return {
            "success": True,
            "data": {
                "model": main_model,
                "imageModel": {
                    "primary": image_model_config.get("primary"),
                    "fallbacks": image_model_config.get("fallbacks", []),
                    "autoSwitch": image_model_config.get("autoSwitch", True)
                },
                "allModels": all_models,
                "visionModels": vision_models
            }
        }

    except Exception as e:
        logger.error(f"[模型管理] 获取模型配置失败: {e}")
        return {"success": False, "error": str(e)}


@router.post("/config")
async def update_model_config(
    request: ModelConfigRequest,
    service: NanobotService = Depends(get_nanobot_service_optional)
):
    """
    更新模型配置

    更新主模型和/或视觉模型配置。

    请求体:
        - model: 主模型名称（可选）
        - imageModel: 视觉模型配置（可选）
            - primary: 首选视觉模型
            - fallbacks: 备选模型列表
            - autoSwitch: 是否自动切换

    响应:
        - success: 是否成功
        - data.message: 成功消息
    """
    try:
        config_data, error = read_config_file()

        if error and "不存在" not in error and "not found" not in error.lower():
            return {"success": False, "error": error}

        config_data = config_data or {}

        # 确保 agents.defaults 存在
        if "agents" not in config_data:
            config_data["agents"] = {}
        if "defaults" not in config_data["agents"]:
            config_data["agents"]["defaults"] = {}

        # 更新主模型
        if request.model:
            config_data["agents"]["defaults"]["model"] = request.model
            logger.info(f"[模型管理] 更新主模型: {request.model}")

        # 更新视觉模型配置
        if request.image_model:
            image_model_config = config_data["agents"]["defaults"].get("imageModel", {})

            if request.image_model.primary is not None:
                image_model_config["primary"] = request.image_model.primary

            if request.image_model.fallbacks is not None:
                image_model_config["fallbacks"] = request.image_model.fallbacks

            if request.image_model.auto_switch is not None:
                image_model_config["autoSwitch"] = request.image_model.auto_switch

            config_data["agents"]["defaults"]["imageModel"] = image_model_config
            logger.info(f"[模型管理] 更新视觉模型配置: {image_model_config}")

        # 写入配置
        success, error = write_config_file(config_data)
        if not success:
            return {"success": False, "error": error}

        # 如果服务已初始化，重新加载
        if service and service.is_initialized:
            await service.reload()

        return {"success": True, "data": {"message": "模型配置已更新"}}

    except Exception as e:
        logger.error(f"[模型管理] 更新模型配置失败: {e}")
        return {"success": False, "error": str(e)}
