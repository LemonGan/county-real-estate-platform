"""
文件上传工具
"""
import os
import uuid
import logging
from pathlib import Path
from typing import Optional, Tuple
from fastapi import UploadFile, HTTPException, status
from PIL import Image
import aiofiles

from app.core.config import settings

logger = logging.getLogger(__name__)


ALLOWED_IMAGE_TYPES = {"image/jpeg", "image/jpg", "image/png", "image/webp"}
ALLOWED_IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp"}


async def save_uploaded_image(
    file: UploadFile,
    subdirectory: str = "properties",
    create_thumbnail: bool = True
) -> Tuple[str, Optional[str], dict]:
    """
    保存上传的图片
    
    Args:
        file: 上传的文件
        subdirectory: 子目录名称
        create_thumbnail: 是否创建缩略图
    
    Returns:
        Tuple[image_url, thumbnail_url, image_info]
        image_info包含: width, height, file_size
    """
    # 验证文件类型
    if file.content_type not in ALLOWED_IMAGE_TYPES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"不支持的文件类型，仅支持: {', '.join(ALLOWED_IMAGE_TYPES)}"
        )
    
    # 验证文件扩展名
    file_ext = Path(file.filename).suffix.lower()
    if file_ext not in ALLOWED_IMAGE_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"不支持的文件扩展名，仅支持: {', '.join(ALLOWED_IMAGE_EXTENSIONS)}"
        )
    
    # 创建上传目录
    upload_dir = Path(settings.UPLOAD_DIR) / subdirectory
    upload_dir.mkdir(parents=True, exist_ok=True)
    
    # 生成唯一文件名
    file_id = uuid.uuid4().hex
    filename = f"{file_id}{file_ext}"
    file_path = upload_dir / filename
    
    # 读取文件内容
    content = await file.read()
    
    # 验证文件大小
    if len(content) > settings.MAX_FILE_SIZE:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"文件大小超过限制（最大 {settings.MAX_FILE_SIZE / 1024 / 1024:.1f}MB）"
        )
    
    # 保存文件
    async with aiofiles.open(file_path, 'wb') as f:
        await f.write(content)
    
    # 获取图片信息并创建缩略图
    thumbnail_url = None
    image_info = {}
    
    try:
        with Image.open(file_path) as img:
            image_info = {
                "width": img.width,
                "height": img.height,
                "file_size": len(content)
            }
            
            # 创建缩略图
            if create_thumbnail:
                thumbnail_dir = upload_dir / "thumbnails"
                thumbnail_dir.mkdir(parents=True, exist_ok=True)
                
                # 生成缩略图（最大宽度300px）
                thumbnail_size = (300, 300)
                img.thumbnail(thumbnail_size, Image.Resampling.LANCZOS)
                
                thumbnail_filename = f"{file_id}_thumb{file_ext}"
                thumbnail_path = thumbnail_dir / thumbnail_filename
                img.save(thumbnail_path, optimize=True, quality=85)
                
                thumbnail_url = f"/static/{subdirectory}/thumbnails/{thumbnail_filename}"
    except Exception as e:
        # 如果图片处理失败，删除已保存的文件
        if file_path.exists():
            file_path.unlink()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"图片处理失败: {str(e)}"
        )
    
    # 生成URL（相对路径，实际部署时需要配置静态文件服务）
    image_url = f"/static/{subdirectory}/{filename}"
    
    return image_url, thumbnail_url, image_info


def get_static_url(path: str) -> str:
    """获取静态文件URL"""
    return f"/static/{path}"


async def delete_uploaded_file(file_url: str) -> bool:
    """
    删除上传的文件
    
    Args:
        file_url: 文件URL（如 /static/properties/xxx.jpg）
    
    Returns:
        True表示删除成功，False表示文件不存在或删除失败
    """
    try:
        # 从URL中提取文件路径
        # /static/properties/xxx.jpg -> properties/xxx.jpg
        if file_url.startswith("/static/"):
            relative_path = file_url[8:]  # 移除 "/static/" 前缀
        else:
            relative_path = file_url
        
        # 构建完整文件路径
        file_path = Path(settings.UPLOAD_DIR) / relative_path
        
        # 检查文件是否存在
        if not file_path.exists():
            return False
        
        # 删除文件
        file_path.unlink()
        return True
    except Exception as e:
        # 记录错误但不抛出异常
        logger.error(f"删除文件失败: {file_url} - {str(e)}")
        return False


async def delete_uploaded_image_with_thumbnail(image_url: str, thumbnail_url: Optional[str] = None) -> bool:
    """
    删除上传的图片及其缩略图
    
    Args:
        image_url: 图片URL
        thumbnail_url: 缩略图URL（可选）
    
    Returns:
        True表示至少一个文件删除成功
    """
    image_deleted = await delete_uploaded_file(image_url)
    thumbnail_deleted = True
    
    if thumbnail_url:
        thumbnail_deleted = await delete_uploaded_file(thumbnail_url)
    
    return image_deleted or thumbnail_deleted
