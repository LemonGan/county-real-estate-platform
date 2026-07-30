"""
房源管理API
"""
from fastapi import APIRouter, Depends, Query, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional, List

from app.core.database import get_db
from app.api.deps import get_current_active_user
from app.models.user import User
from app.schemas.property import (
    PropertyCreate, PropertyResponse, PropertyListResponse, PropertyUpdate
)
from app.crud.property import (
    create_property, get_properties, get_property_by_id,
    update_property, delete_property
)

router = APIRouter()


@router.post("", response_model=PropertyResponse, status_code=201, summary="创建房源")
async def create_property_endpoint(
    property_data: PropertyCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """创建新房源；只有已审核通过的经纪人可投稿，投稿默认待审核。"""
    if not current_user.is_agent or current_user.agent_application_status != "approved":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="只有审核通过的经纪人可以发布房源")
    property = await create_property(db, property_data, current_user.id)
    return property


@router.get("", response_model=PropertyListResponse, summary="获取房源列表")
async def get_properties_list(
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(10, ge=1, le=100, description="每页数量"),
    city: Optional[str] = Query(None, description="城市筛选"),
    district: Optional[str] = Query(None, description="区县筛选"),
    min_price: Optional[int] = Query(None, ge=0, description="最低价格（元）"),
    max_price: Optional[int] = Query(None, ge=0, description="最高价格（元）"),
    min_area: Optional[float] = Query(None, ge=0, description="最小面积（㎡）"),
    max_area: Optional[float] = Query(None, ge=0, description="最大面积（㎡）"),
    rooms: Optional[str] = Query(None, description="户型筛选"),
    property_type: Optional[int] = Query(None, description="房产类型：1住宅，2商铺，3写字楼，4别墅"),
    transaction_type: Optional[int] = Query(None, description="交易类型：1出售，2出租"),
    status_filter: Optional[int] = Query(None, description="公开列表仅支持在售状态（1）"),
    keyword: Optional[str] = Query(None, description="关键词搜索（搜索标题、描述、地址、城市、区县）"),
    db: AsyncSession = Depends(get_db)
):
    """获取公开房源列表：仅返回已审核且在售的记录。"""
    if status_filter not in (None, 1):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="公开列表仅支持查询在售房源",
        )
    # 转换户型
    rooms_int = int(rooms) if rooms else None

    properties, total = await get_properties(
        db,
        page=page,
        page_size=page_size,
        city=city,
        district=district,
        min_price=min_price,
        max_price=max_price,
        min_area=min_area,
        max_area=max_area,
        rooms=rooms_int,
        property_type=property_type,
        transaction_type=transaction_type,
        status=1,
        keyword=keyword
    )
    return {
        "list": properties,
        "total": total,
        "page": page,
        "page_size": page_size
    }


@router.get("/nearby/", response_model=PropertyListResponse, summary="获取附近房源")
async def get_nearby_properties(
    longitude: float = Query(..., description="经度"),
    latitude: float = Query(..., description="纬度"),
    radius: int = Query(5000, ge=100, le=50000, description="搜索半径（米）"),
    max_distance: Optional[int] = Query(None, ge=100, le=50000, description="最大距离（米）"),
    min_price: Optional[int] = Query(None, ge=0, description="最低价格（万）"),
    max_price: Optional[int] = Query(None, ge=0, description="最高价格（万）"),
    min_area: Optional[float] = Query(None, ge=0, description="最小面积（㎡）"),
    max_area: Optional[float] = Query(None, ge=0, description="最大面积（㎡）"),
    rooms: Optional[str] = Query(None, description="户型筛选"),
    property_type: Optional[str] = Query(None, description="房源类型"),
    db: AsyncSession = Depends(get_db)
):
    """
    根据地理位置获取附近房源
    支持价格、面积、户型、类型、距离等筛选条件
    """
    # 转换价格单位（前端传万，后端存元）
    min_price_yuan = min_price * 10000 if min_price else None
    max_price_yuan = max_price * 10000 if max_price else None

    # 转换户型
    rooms_int = int(rooms) if rooms else None

    # 使用 max_distance 参数（如果提供了）或 radius 参数
    distance_limit = max_distance if max_distance is not None else radius

    properties, total = await get_properties(
        db,
        page=1,
        page_size=100,  # 地图模式返回更多
        min_price=min_price_yuan,
        max_price=max_price_yuan,
        min_area=min_area,
        max_area=max_area,
        rooms=rooms_int,
        property_type=int(property_type) if property_type else None,
        status=1,  # 只返回在售房源
        user_lat=latitude,
        user_lon=longitude,
        max_distance=distance_limit
    )

    return {
        "list": properties,
        "total": total,
        "page": 1,
        "page_size": 100
    }


@router.get("/mine", response_model=PropertyListResponse, summary="获取我的房源（含待审核状态）")
async def get_my_properties(
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    status_filter: Optional[int] = Query(None, ge=1, le=3),
    audit_status: Optional[int] = Query(None, ge=0, le=2),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    properties, total = await get_properties(
        db, page=page, page_size=page_size, status=status_filter,
        agent_id=current_user.id, audit_status=audit_status, only_approved=False,
    )
    return {"list": properties, "total": total, "page": page, "page_size": page_size}


@router.get("/mine/{property_id}", response_model=PropertyResponse, summary="获取我可编辑的房源")
async def get_my_property_detail(
    property_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """获取当前经纪人自己的房源，允许读取待审核或被拒绝的记录以便修正。"""
    property = await get_property_by_id(db, property_id=property_id)
    if not property:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="房源不存在",
        )
    if property.agent_id != current_user.id and not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="无权查看此房源",
        )
    return property


@router.get("/{property_id}", response_model=PropertyResponse, summary="获取房源详情")
async def get_property_detail(
    property_id: int,
    db: AsyncSession = Depends(get_db)
):
    """根据ID获取房源详细信息"""
    property = await get_property_by_id(db, property_id=property_id)
    if not property or property.audit_status != 1 or property.status != 1:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="房源不存在"
        )
    return property


@router.put("/{property_id}", response_model=PropertyResponse, summary="修改房源信息")
async def update_property_endpoint(
    property_id: int,
    property_data: PropertyUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """修改房源信息（仅房源发布者可修改）"""
    property = await get_property_by_id(db, property_id=property_id)
    if not property:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="房源不存在"
        )
    
    # 检查权限：只有发布者可以修改
    if property.agent_id != current_user.id and not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="无权修改此房源"
        )
    
    update_data = property_data.model_dump(exclude_unset=True)
    if update_data:
        # 已通过的公开房源一旦改动，必须重新审核后才能再次展示。
        update_data.update({
            "audit_status": 0,
            "status": 3,
            "audit_reviewed_at": None,
            "audit_reviewed_by": None,
            "audit_review_note": None,
        })
    updated_property = await update_property(
        db,
        property_id=property_id,
        property_data=update_data
    )
    return updated_property


@router.delete("/{property_id}", status_code=204, summary="删除房源")
async def delete_property_endpoint(
    property_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """删除房源（软删除，仅房源发布者可删除）"""
    property = await get_property_by_id(db, property_id=property_id)
    if not property:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="房源不存在"
        )
    
    # 检查权限：只有发布者可以删除
    if property.agent_id != current_user.id and not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="无权删除此房源"
        )
    
    success = await delete_property(db, property_id=property_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="删除失败"
        )
    
    return None


@router.patch("/{property_id}/status", response_model=PropertyResponse, summary="更新房源状态")
async def update_property_status(
    property_id: int,
    new_status: int = Query(..., ge=1, le=3, description="新状态：1在售，2已售，3下架"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """更新房源状态（仅房源发布者可操作）"""
    property = await get_property_by_id(db, property_id=property_id)
    if not property:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="房源不存在"
        )

    # 检查权限
    if property.agent_id != current_user.id and not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="无权修改此房源状态"
        )

    if new_status == 1 and property.audit_status != 1:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="房源通过审核后才能设置为在售",
        )

    updated_property = await update_property(
        db,
        property_id=property_id,
        property_data={"status": new_status}
    )
    return updated_property
