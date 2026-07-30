"""
房源评价API - 嵌套路由
"""
from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_
from typing import Optional, List
from pydantic import BaseModel, Field

from app.core.database import get_db
from app.api.deps import get_current_active_user
from app.models.user import User
from app.models.property import Property
from app.models.property_review import PropertyReview

router = APIRouter()


class ReviewCreate(BaseModel):
    rating: float = Field(..., ge=1, le=5)
    content: Optional[str] = Field(default=None, max_length=500)
    images: Optional[List[str]] = None


@router.get("/reviews/my", summary="获取当前用户的房源评价")
async def get_my_reviews(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    result = await db.execute(
        select(PropertyReview)
        .where(PropertyReview.user_id == current_user.id)
        .order_by(PropertyReview.created_at.desc())
    )
    reviews = result.scalars().all()
    return {
        "list": [
            {
                "id": review.id,
                "property_id": review.property_id,
                "rating": review.rating,
                "status": review.status,
                "is_verified": review.is_verified,
                "created_at": review.created_at.isoformat() if review.created_at else None,
            }
            for review in reviews
        ]
    }


@router.get("/{property_id}/reviews", summary="获取房源评价列表")
async def get_reviews(
    property_id: int,
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    db: AsyncSession = Depends(get_db)
):
    """获取指定房源的评价列表"""
    query = select(PropertyReview).where(
        and_(
            PropertyReview.property_id == property_id,
            PropertyReview.status == 1,
            PropertyReview.is_verified == 1
        )
    ).order_by(PropertyReview.created_at.desc())
    
    # 总数
    count_query = select(func.count()).select_from(query.subquery())
    result = await db.execute(count_query)
    total = result.scalar() or 0
    
    # 分页
    offset = (page - 1) * page_size
    query = query.offset(offset).limit(page_size)
    result = await db.execute(query)
    reviews = result.scalars().all()
    
    # 评分统计
    stats_query = select(
        func.avg(PropertyReview.rating).label("avg_rating"),
        func.count(PropertyReview.id).label("total_count")
    ).where(
        and_(
            PropertyReview.property_id == property_id,
            PropertyReview.status == 1,
            PropertyReview.is_verified == 1
        )
    )
    result = await db.execute(stats_query)
    stats = result.one()
    
    review_list = []
    for r in reviews:
        user_query = select(User).where(User.id == r.user_id)
        result = await db.execute(user_query)
        user = result.scalar_one_or_none()
        
        review_list.append({
            "id": r.id,
            "user_id": r.user_id,
            "user_nickname": user.nickname if user else "匿名用户",
            "user_avatar": user.avatar if user else "",
            "rating": r.rating,
            "content": r.content,
            "images": r.images.split(",") if r.images else [],
            "created_at": r.created_at.isoformat() if r.created_at else None
        })
    
    return {
        "list": review_list,
        "total": total,
        "page": page,
        "page_size": page_size,
        "avg_rating": round(stats.avg_rating, 1) if stats.avg_rating else 0,
        "total_count": stats.total_count or 0
    }


@router.post("/{property_id}/reviews", summary="添加房源评价")
async def create_review(
    property_id: int,
    review_data: ReviewCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """用户添加房源评价"""
    # 检查房源是否存在
    prop_query = select(Property).where(Property.id == property_id)
    result = await db.execute(prop_query)
    property_obj = result.scalar_one_or_none()
    
    if not property_obj:
        raise HTTPException(status_code=404, detail="房源不存在")
    
    # 检查用户是否已评价
    existing_query = select(PropertyReview).where(
        and_(
            PropertyReview.property_id == property_id,
            PropertyReview.user_id == current_user.id
        )
    )
    result = await db.execute(existing_query)
    existing = result.scalar_one_or_none()
    
    if existing:
        raise HTTPException(status_code=400, detail="您已评价过该房源")
    
    # 创建评价
    review = PropertyReview(
        property_id=property_id,
        user_id=current_user.id,
        rating=review_data.rating,
        content=review_data.content,
        images=",".join(review_data.images) if review_data.images else None,
        status=1,
        is_verified=0  # 需要审核
    )
    db.add(review)
    await db.commit()
    await db.refresh(review)
    
    return {
        "id": review.id,
        "message": "评价提交成功，等待审核"
    }
