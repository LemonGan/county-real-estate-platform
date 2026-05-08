"""
文件上传API
"""
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.api.deps import get_current_active_user
from app.models.user import User
from app.utils.upload import save_uploaded_image

router = APIRouter()


@router.post("/upload", summary="上传文件")
async def upload_file(
    file: UploadFile = File(..., description="上传的文件"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """通用文件上传接口"""
    try:
        image_url, thumbnail_url, image_info = await save_uploaded_image(
            file,
            subdirectory="properties",
            create_thumbnail=False
        )
        return {
            "url": image_url,
            "thumbnail_url": thumbnail_url,
            "filename": file.filename,
            "size": image_info.get("file_size"),
            "width": image_info.get("width"),
            "height": image_info.get("height")
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"文件上传失败: {str(e)}"
        )
