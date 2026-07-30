"""
房源图片管理API
"""
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List

from app.core.database import get_db
from app.api.deps import get_current_active_user
from app.models.user import User
from app.schemas.property_image import (
    PropertyImageResponse, PropertyImageListResponse, PropertyImageUpdate
)
from app.crud.property_image import (
    get_property_images, create_property_image, delete_property_image,
    update_property_image, set_cover_image, get_property_image_by_id
)
from app.crud.property import get_property_by_id
from app.utils.upload import save_uploaded_image

router = APIRouter()


async def _request_reaudit(property) -> None:
    """图片变化会影响公开展示内容，已通过房源需重新审核。"""
    if property.audit_status == 1:
        property.audit_status = 0
        property.status = 3
        property.audit_reviewed_at = None
        property.audit_reviewed_by = None
        property.audit_review_note = None
        await db.commit()
        await db.refresh(property)


@router.post("/properties/{property_id}/images", response_model=PropertyImageResponse, status_code=201, summary="上传房源图片")
async def upload_property_image(
    property_id: int,
    file: UploadFile = File(..., description="图片文件"),
    image_type: int = Query(0, ge=0, le=5, description="图片类型：0普通，1客厅，2卧室，3厨房，4卫生间，5阳台"),
    sort_order: int = Query(0, description="排序顺序"),
    is_cover: bool = Query(False, description="是否设为封面"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """上传房源图片（仅房源发布者可上传）"""
    # 检查房源是否存在
    property = await get_property_by_id(db, property_id)
    if not property:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="房源不存在"
        )
    
    # 检查权限：只有发布者可以上传图片
    if property.agent_id != current_user.id and not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="无权上传此房源的图片"
        )
    
    # 保存图片
    try:
        image_url, thumbnail_url, image_info = await save_uploaded_image(
            file,
            subdirectory="properties",
            create_thumbnail=True
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"图片上传失败: {str(e)}"
        )
    
    # 创建图片记录
    db_image = await create_property_image(
        db,
        property_id=property_id,
        image_url=image_url,
        thumbnail_url=thumbnail_url,
        image_type=image_type,
        sort_order=sort_order,
        is_cover=is_cover,
        file_size=image_info.get("file_size"),
        width=image_info.get("width"),
        height=image_info.get("height")
    )
    await _request_reaudit(property)
    
    return db_image


@router.get("/properties/{property_id}/images", response_model=PropertyImageListResponse, summary="获取房源图片列表")
async def get_property_images_list(
    property_id: int,
    db: AsyncSession = Depends(get_db)
):
    """获取房源的所有图片"""
    images = await get_property_images(db, property_id)
    return {
        "list": images,
        "total": len(images)
    }


@router.get("/images/{image_id}", response_model=PropertyImageResponse, summary="获取图片详情")
async def get_property_image_detail(
    image_id: int,
    db: AsyncSession = Depends(get_db)
):
    """根据ID获取图片详细信息"""
    image = await get_property_image_by_id(db, image_id)
    if not image:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="图片不存在"
        )
    return image


@router.put("/images/{image_id}", response_model=PropertyImageResponse, summary="更新图片信息")
async def update_property_image_info(
    image_id: int,
    image_data: PropertyImageUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """更新图片信息（仅房源发布者可操作）"""
    image = await get_property_image_by_id(db, image_id)
    if not image:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="图片不存在"
        )
    
    # 检查权限
    property = await get_property_by_id(db, image.property_id)
    if not property or (property.agent_id != current_user.id and not current_user.is_superuser):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="无权修改此图片"
        )
    
    updated_image = await update_property_image(
        db,
        image_id=image_id,
        image_type=image_data.image_type,
        sort_order=image_data.sort_order,
        is_cover=image_data.is_cover
    )
    await _request_reaudit(property)
    return updated_image


@router.delete("/images/{image_id}", status_code=204, summary="删除图片")
async def delete_property_image_endpoint(
    image_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """删除图片（仅房源发布者可删除）"""
    image = await get_property_image_by_id(db, image_id)
    if not image:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="图片不存在"
        )
    
    # 检查权限
    property = await get_property_by_id(db, image.property_id)
    if not property or (property.agent_id != current_user.id and not current_user.is_superuser):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="无权删除此图片"
        )
    
    success = await delete_property_image(db, image_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="删除失败"
        )
    
    await _request_reaudit(property)
    return None


@router.patch("/properties/{property_id}/images/{image_id}/cover", response_model=PropertyImageResponse, summary="设置封面图")
async def set_property_cover_image(
    property_id: int,
    image_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """设置房源封面图（仅房源发布者可操作）"""
    # 检查权限
    property = await get_property_by_id(db, property_id)
    if not property:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="房源不存在"
        )
    
    if property.agent_id != current_user.id and not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="无权设置此房源的封面图"
        )
    
    success = await set_cover_image(db, property_id, image_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="设置封面图失败，请检查图片是否属于该房源"
        )
    
    image = await get_property_image_by_id(db, image_id)
    await _request_reaudit(property)
    return image
