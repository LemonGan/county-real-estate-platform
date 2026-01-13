"""
推荐算法工具函数
"""
from decimal import Decimal
from typing import Optional, Dict, Any
from datetime import datetime, timedelta

from app.models.user_preference import UserPreference
from app.models.short_video import ShortVideo
from app.models.user_behavior import UserBehavior
from app.models.property import Property


def calculate_base_score(video: ShortVideo) -> Decimal:
    """
    计算基础得分
    基于视频的统计数据和发布状态
    """
    score = Decimal('0.5')  # 基础分
    
    # 播放量得分（对数缩放，避免头部效应）
    if video.view_count > 0:
        import math
        view_score = min(Decimal(str(math.log10(video.view_count + 1) / 3)), Decimal('0.3'))
        score += view_score
    
    # 互动率得分（点赞+评论+分享+收藏）
    total_engagement = video.like_count + video.comment_count + video.share_count + video.favorite_count
    if video.view_count > 0:
        engagement_rate = Decimal(str(total_engagement)) / Decimal(str(video.view_count))
        engagement_score = min(engagement_rate * Decimal('0.2'), Decimal('0.2'))
        score += engagement_score
    
    # 已发布状态加分
    if video.is_published:
        score += Decimal('0.1')
    
    return min(score, Decimal('1.0'))


def calculate_user_preference_score(
    user_preference: Optional[UserPreference],
    video: ShortVideo,
    property: Optional[Property] = None
) -> Decimal:
    """
    计算用户偏好得分
    基于用户偏好设置和视频/房源特征匹配度
    """
    if not user_preference:
        return Decimal('0.5')  # 无偏好时返回中性分
    
    score = Decimal('0.0')
    total_weight = Decimal('0.0')
    
    # 如果有关联房源，计算房源匹配度
    if property and user_preference:
        # 价格匹配度
        if user_preference.budget_min and user_preference.budget_max and property.total_price:
            price = property.total_price / 10000  # 转换为万元
            if user_preference.budget_min <= price <= user_preference.budget_max:
                price_match = Decimal('1.0')
            elif price < user_preference.budget_min:
                # 低于预算，给予部分分数
                price_match = Decimal(str(max(0, 1 - (user_preference.budget_min - price) / user_preference.budget_min)))
            else:
                # 高于预算，给予部分分数
                price_match = Decimal(str(max(0, 1 - (price - user_preference.budget_max) / user_preference.budget_max)))
            
            weight = Decimal(str(user_preference.price_weight or 0.3))
            score += price_match * weight
            total_weight += weight
        
        # 面积匹配度
        if user_preference.area_min and user_preference.area_max and property.area:
            if user_preference.area_min <= property.area <= user_preference.area_max:
                area_match = Decimal('1.0')
            elif property.area < user_preference.area_min:
                area_match = Decimal(str(max(0, 1 - (user_preference.area_min - property.area) / user_preference.area_min)))
            else:
                area_match = Decimal(str(max(0, 1 - (property.area - user_preference.area_max) / user_preference.area_max)))
            
            weight = Decimal('0.2')  # 面积权重
            score += area_match * weight
            total_weight += weight
        
        # 户型类型匹配度
        if user_preference.preferred_property_types and property.property_type:
            if property.property_type in user_preference.preferred_property_types:
                type_match = Decimal('1.0')
            else:
                type_match = Decimal('0.3')  # 不完全匹配给予部分分数
            
            weight = Decimal('0.2')
            score += type_match * weight
            total_weight += weight
        
        # 位置匹配度
        if user_preference.preferred_locations and property.city:
            if property.city in user_preference.preferred_locations or property.district in (user_preference.preferred_locations or []):
                location_match = Decimal('1.0')
            else:
                location_match = Decimal('0.2')
            
            weight = Decimal(str(user_preference.location_weight or 0.3))
            score += location_match * weight
            total_weight += weight
    
    # 归一化得分
    if total_weight > 0:
        normalized_score = score / total_weight
    else:
        normalized_score = Decimal('0.5')
    
    return min(normalized_score, Decimal('1.0'))


def calculate_location_score(
    user_city: Optional[str],
    video: ShortVideo,
    property: Optional[Property] = None
) -> Decimal:
    """
    计算地理位置得分
    基于用户当前城市和视频关联房源的位置
    """
    if not user_city or not property:
        return Decimal('0.5')
    
    # 完全匹配
    if property.city == user_city:
        return Decimal('1.0')
    
    # 同省不同市（假设有省份信息）
    # 这里简化处理，可以根据实际需求扩展
    return Decimal('0.3')


def calculate_recency_score(video: ShortVideo) -> Decimal:
    """
    计算时效性得分
    基于视频发布时间，越新得分越高
    """
    if not video.publish_time:
        return Decimal('0.3')  # 未发布视频得分较低
    
    now = datetime.now(video.publish_time.tzinfo)
    days_old = (now - video.publish_time).days
    
    # 7天内：1.0分
    # 30天内：0.8分
    # 90天内：0.5分
    # 超过90天：0.3分
    if days_old <= 7:
        return Decimal('1.0')
    elif days_old <= 30:
        return Decimal('0.8')
    elif days_old <= 90:
        return Decimal('0.5')
    else:
        return Decimal('0.3')


def calculate_engagement_score(video: ShortVideo) -> Decimal:
    """
    计算互动率得分
    基于视频的点赞、评论、分享、收藏数据
    """
    if video.view_count == 0:
        return Decimal('0.3')
    
    total_engagement = video.like_count + video.comment_count + video.share_count + video.favorite_count
    engagement_rate = Decimal(str(total_engagement)) / Decimal(str(video.view_count))
    
    # 互动率 > 10%: 1.0分
    # 互动率 > 5%: 0.8分
    # 互动率 > 2%: 0.6分
    # 互动率 > 1%: 0.4分
    # 其他: 0.3分
    if engagement_rate >= Decimal('0.10'):
        return Decimal('1.0')
    elif engagement_rate >= Decimal('0.05'):
        return Decimal('0.8')
    elif engagement_rate >= Decimal('0.02'):
        return Decimal('0.6')
    elif engagement_rate >= Decimal('0.01'):
        return Decimal('0.4')
    else:
        return Decimal('0.3')


def calculate_final_score(
    base_score: Decimal,
    user_preference_score: Decimal,
    location_score: Decimal,
    recency_score: Decimal,
    engagement_score: Decimal,
    weights: Optional[Dict[str, Decimal]] = None
) -> Decimal:
    """
    计算最终推荐得分
    使用加权平均
    """
    if weights is None:
        weights = {
            'base': Decimal('0.2'),
            'preference': Decimal('0.3'),
            'location': Decimal('0.2'),
            'recency': Decimal('0.15'),
            'engagement': Decimal('0.15')
        }
    
    final_score = (
        base_score * weights['base'] +
        user_preference_score * weights['preference'] +
        location_score * weights['location'] +
        recency_score * weights['recency'] +
        engagement_score * weights['engagement']
    )
    
    return min(final_score, Decimal('1.0'))
