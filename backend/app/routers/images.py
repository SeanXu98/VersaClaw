# -*- coding: utf-8 -*-
"""
图片上传 API 路由模块

该模块提供图片上传相关的 API 端点：
- POST /api/upload/image: 上传图片
- GET /api/upload/image/{image_id}: 获取图片
- GET /api/upload/image/{image_id}/thumbnail: 获取缩略图
- DELETE /api/upload/image/{image_id}: 删除图片

支持的图片格式：PNG、JPEG、GIF、WebP
最大文件大小：10MB
"""
import logging
from fastapi import APIRouter, UploadFile, File, HTTPException, Depends
from fastapi.responses import FileResponse

from app.services.image_service import ImageService
from app.dependencies import get_image_service
from app.models.schemas import UploadResponse

# 配置日志
logger = logging.getLogger(__name__)

# 创建路由器
router = APIRouter(prefix="/api/upload/image", tags=["图片上传"])


@router.post("", response_model=UploadResponse)
async def upload_image(
    file: UploadFile = File(...),
    service: ImageService = Depends(get_image_service)
):
    """
    上传图片

    上传单张图片到服务器，返回图片的唯一标识和访问 URL。

    请求:
        - Content-Type: multipart/form-data
        - file: 图片文件

    响应:
        - success: 是否上传成功
        - data: 图片信息（id, url, thumbnail_url, size, mime_type, width, height）
        - error: 错误信息（失败时）
    """
    # 验证文件类型
    if file.content_type not in service.allowed_types:
        return UploadResponse(
            success=False,
            error=f"不支持的文件类型: {file.content_type}。支持的类型: {', '.join(service.allowed_types)}"
        )

    # 读取文件内容
    content = await file.read()

    # 验证文件大小
    is_valid, error = service.validate_image(file.content_type, len(content))
    if not is_valid:
        return UploadResponse(success=False, error=error)

    try:
        # 保存图片
        result = service.save_image(content, file.filename or "image.png", file.content_type)
        logger.info(f"[图片上传] 上传成功: {result['id']}, 文件名: {file.filename}")

        return UploadResponse(success=True, data=result)

    except Exception as e:
        logger.error(f"[图片上传] 上传失败: {e}")
        return UploadResponse(success=False, error=f"上传失败: {str(e)}")


@router.get("/{image_id}")
async def get_image(
    image_id: str,
    service: ImageService = Depends(get_image_service)
):
    """
    获取图片

    根据图片 ID 获取原始图片文件。

    参数:
        - image_id: 图片唯一标识

    返回:
        - 图片文件（二进制流）
    """
    file_path = service.find_image(image_id)
    if not file_path:
        raise HTTPException(status_code=404, detail="图片不存在")

    ext = file_path.suffix.lstrip(".")
    return FileResponse(
        path=file_path,
        media_type=f"image/{ext}",
        filename=f"{image_id}{file_path.suffix}"
    )


@router.get("/{image_id}/thumbnail")
async def get_image_thumbnail(
    image_id: str,
    service: ImageService = Depends(get_image_service)
):
    """
    获取图片缩略图

    根据图片 ID 获取缩略图（最大 200x200 像素）。
    如果缩略图不存在，会自动生成。

    参数:
        - image_id: 图片唯一标识

    返回:
        - 缩略图文件（JPEG 格式）
    """
    # 尝试查找已存在的缩略图
    thumb_path = service.find_thumbnail(image_id)
    if thumb_path:
        return FileResponse(
            path=thumb_path,
            media_type="image/jpeg",
            filename=f"{image_id}_thumb.jpg"
        )

    # 查找原图
    original_path = service.find_image(image_id)
    if not original_path:
        raise HTTPException(status_code=404, detail="图片不存在")

    # 尝试生成缩略图
    thumb_path = service.generate_thumbnail(image_id)
    if thumb_path:
        return FileResponse(
            path=thumb_path,
            media_type="image/jpeg",
            filename=f"{image_id}_thumb.jpg"
        )

    # 回退：返回原图
    logger.warning(f"[图片上传] 无法生成缩略图，返回原图: {image_id}")
    ext = original_path.suffix.lstrip(".")
    return FileResponse(
        path=original_path,
        media_type=f"image/{ext}",
        filename=f"{image_id}{original_path.suffix}"
    )


@router.delete("/{image_id}")
async def delete_image(
    image_id: str,
    service: ImageService = Depends(get_image_service)
):
    """
    删除图片

    删除指定图片及其缩略图。

    参数:
        - image_id: 图片唯一标识

    响应:
        - success: 是否删除成功
        - data.message: 成功消息
    """
    deleted = service.delete_image(image_id)

    if deleted:
        return {"success": True, "data": {"message": "图片已删除"}}
    else:
        raise HTTPException(status_code=404, detail="图片不存在")
