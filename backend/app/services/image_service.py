# -*- coding: utf-8 -*-
"""
图片服务模块

该模块负责处理所有图片相关的业务逻辑，包括：
- 图片上传和存储
- 缩略图生成
- 图片检索
- Base64 编码（用于多模态消息）

使用方式:
    from app.services.image_service import image_service

    # 保存图片
    result = image_service.save_image(content, "test.png", "image/png")
"""
import uuid
import base64
import logging
from pathlib import Path
from typing import Optional, Tuple, List

from app.config import settings
from app.models.schemas import ImageData

# 配置日志
logger = logging.getLogger(__name__)


class ImageService:
    """
    图片服务类

    提供图片上传、存储、检索、缩略图生成等功能。

    属性:
        upload_dir: 图片上传目录
        thumbnail_dir: 缩略图目录
        max_file_size: 最大文件大小（字节）
        allowed_types: 允许的图片 MIME 类型列表
    """

    def __init__(self):
        """初始化图片服务，从配置加载参数"""
        self.upload_dir = settings.UPLOAD_DIR
        self.thumbnail_dir = settings.THUMBNAIL_DIR
        self.max_file_size = settings.MAX_FILE_SIZE
        self.allowed_types = settings.ALLOWED_IMAGE_TYPES

    def ensure_dirs(self) -> None:
        """确保上传目录和缩略图目录存在"""
        self.upload_dir.mkdir(parents=True, exist_ok=True)
        self.thumbnail_dir.mkdir(parents=True, exist_ok=True)

    def validate_image(self, content_type: str, content_size: int) -> Tuple[bool, Optional[str]]:
        """
        验证图片类型和大小

        参数:
            content_type: 图片的 MIME 类型
            content_size: 图片大小（字节）

        返回:
            Tuple[bool, Optional[str]]: (是否有效, 错误信息)
        """
        if content_type not in self.allowed_types:
            return False, f"不支持的文件类型: {content_type}。支持的类型: {', '.join(self.allowed_types)}"

        if content_size > self.max_file_size:
            return False, f"文件太大，最大允许 {self.max_file_size / 1024 / 1024}MB"

        return True, None

    def save_image(self, content: bytes, original_filename: str, content_type: str) -> dict:
        """
        保存上传的图片

        参数:
            content: 图片二进制数据
            original_filename: 原始文件名
            content_type: MIME 类型

        返回:
            dict: 包含图片元数据的字典
        """
        self.ensure_dirs()

        # 生成唯一 ID
        image_id = str(uuid.uuid4())

        # 确定文件扩展名
        ext = Path(original_filename).suffix.lower() or ".png"

        # 保存文件
        file_path = self.upload_dir / f"{image_id}{ext}"
        with open(file_path, "wb") as f:
            f.write(content)

        # 获取图片尺寸（如果可能）
        width, height = self._get_image_dimensions(file_path)

        logger.info(f"[图片服务] 保存图片成功: {image_id}, 文件名: {original_filename}, 大小: {len(content)} 字节")

        return {
            "id": image_id,
            "filename": original_filename,
            "url": f"/api/upload/image/{image_id}",
            "thumbnail_url": f"/api/upload/image/{image_id}/thumbnail",
            "size": len(content),
            "mime_type": content_type,
            "width": width,
            "height": height
        }

    def _get_image_dimensions(self, file_path: Path) -> Tuple[Optional[int], Optional[int]]:
        """
        获取图片尺寸（使用 Pillow）

        参数:
            file_path: 图片文件路径

        返回:
            Tuple[Optional[int], Optional[int]]: (宽度, 高度)，失败则返回 (None, None)
        """
        try:
            from PIL import Image
            img = Image.open(file_path)
            width, height = img.size
            img.close()
            return width, height
        except ImportError:
            logger.warning("[图片服务] Pillow 未安装，无法获取图片尺寸")
            return None, None
        except Exception as e:
            logger.warning(f"[图片服务] 获取图片尺寸失败: {e}")
            return None, None

    def find_image(self, image_id: str) -> Optional[Path]:
        """
        根据 ID 查找图片文件

        参数:
            image_id: 图片 ID

        返回:
            Optional[Path]: 图片文件路径，未找到则返回 None
        """
        for ext in [".png", ".jpg", ".jpeg", ".gif", ".webp", ""]:
            file_path = self.upload_dir / f"{image_id}{ext}"
            if file_path.exists():
                return file_path
        return None

    def find_thumbnail(self, image_id: str) -> Optional[Path]:
        """
        根据 ID 查找缩略图文件

        参数:
            image_id: 图片 ID

        返回:
            Optional[Path]: 缩略图文件路径，未找到则返回 None
        """
        for ext in [".jpg", ".png", ""]:
            thumb_path = self.thumbnail_dir / f"{image_id}_thumb{ext}"
            if thumb_path.exists():
                return thumb_path
        return None

    def generate_thumbnail(self, image_id: str) -> Optional[Path]:
        """
        为图片生成缩略图

        参数:
            image_id: 图片 ID

        返回:
            Optional[Path]: 生成的缩略图路径，失败则返回 None
        """
        self.ensure_dirs()

        # 查找原图
        original_path = self.find_image(image_id)
        if not original_path:
            logger.warning(f"[图片服务] 找不到原图，无法生成缩略图: {image_id}")
            return None

        try:
            from PIL import Image

            img = Image.open(original_path)
            img.thumbnail((200, 200))

            thumb_path = self.thumbnail_dir / f"{image_id}_thumb.jpg"
            img.convert("RGB").save(thumb_path, "JPEG", quality=85)
            img.close()

            logger.info(f"[图片服务] 生成缩略图成功: {image_id}")
            return thumb_path

        except ImportError:
            logger.warning("[图片服务] Pillow 未安装，无法生成缩略图")
            return None
        except Exception as e:
            logger.error(f"[图片服务] 生成缩略图失败: {e}")
            return None

    def delete_image(self, image_id: str) -> bool:
        """
        删除图片及其缩略图

        参数:
            image_id: 图片 ID

        返回:
            bool: 是否成功删除图片
        """
        deleted = False

        # 删除原图
        for ext in [".png", ".jpg", ".jpeg", ".gif", ".webp", ""]:
            file_path = self.upload_dir / f"{image_id}{ext}"
            if file_path.exists():
                file_path.unlink()
                deleted = True
                break

        # 删除缩略图
        for ext in [".jpg", ".png", ""]:
            thumb_path = self.thumbnail_dir / f"{image_id}_thumb{ext}"
            if thumb_path.exists():
                thumb_path.unlink()

        if deleted:
            logger.info(f"[图片服务] 删除图片成功: {image_id}")
        else:
            logger.warning(f"[图片服务] 删除图片失败，未找到: {image_id}")

        return deleted

    def load_as_base64(self, image_id: str) -> Tuple[Optional[str], Optional[str]]:
        """
        加载图片并转换为 Base64 编码

        参数:
            image_id: 图片 ID

        返回:
            Tuple[Optional[str], Optional[str]]: (base64 字符串, MIME 类型)，失败则返回 (None, None)
        """
        file_path = self.find_image(image_id)
        if not file_path:
            return None, None

        try:
            with open(file_path, "rb") as f:
                image_data = f.read()

            # 确定 MIME 类型
            ext = file_path.suffix.lower()
            mime_type_map = {
                ".png": "image/png",
                ".jpg": "image/jpeg",
                ".jpeg": "image/jpeg",
                ".gif": "image/gif",
                ".webp": "image/webp"
            }
            mime_type = mime_type_map.get(ext, "image/png")

            base64_string = base64.b64encode(image_data).decode("utf-8")
            return base64_string, mime_type

        except Exception as e:
            logger.error(f"[图片服务] 加载图片失败 {image_id}: {e}")
            return None, None

    def build_multimodal_content(self, message: str, images: Optional[List[ImageData]] = None) -> list:
        """
        构建多模态消息内容（OpenAI 格式）

        参数:
            message: 文本消息
            images: 图片数据列表

        返回:
            list: 内容块列表，格式为 [{"type": "text", "text": "..."}, {"type": "image_url", ...}]
        """
        content = [{"type": "text", "text": message}]

        if images:
            for img in images:
                try:
                    # 如果 URL 已经是 base64 data URL，直接使用
                    if img.url and img.url.startswith("data:"):
                        content.append({
                            "type": "image_url",
                            "image_url": {"url": img.url}
                        })
                    else:
                        # 从服务器加载并转换为 base64
                        base64_data, mime_type = self.load_as_base64(img.id)
                        if base64_data and mime_type:
                            content.append({
                                "type": "image_url",
                                "image_url": {"url": f"data:{mime_type};base64,{base64_data}"}
                            })
                except Exception as e:
                    logger.error(f"[图片服务] 加载图片失败 {img.id}: {e}")
                    # 跳过加载失败的图片

        return content


# 全局服务实例
image_service = ImageService()
