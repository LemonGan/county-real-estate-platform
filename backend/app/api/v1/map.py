"""
地图相关API
使用腾讯地图API实现位置搜索
"""
from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional, List
from httpx import AsyncClient
from app.core.database import get_db
from app.core.config import settings

router = APIRouter()


@router.get("/search", summary="搜索位置")
async def search_location(
    keyword: str = Query(..., min_length=1, description="搜索关键词"),
    city: Optional[str] = Query(None, description="限定城市，如'钦州市'"),
    region: Optional[str] = Query(None, description="限定区域"),
):
    """
    使用腾讯地图API搜索位置

    参数:
    - keyword: 搜索关键词（地点名称、地址等）
    - city: 限定城市
    - region: 限定区域

    返回位置列表，包含名称、地址、经纬度等信息
    """
    if not settings.TENCENT_MAP_KEY:
        raise HTTPException(status_code=503, detail="地图搜索服务暂未配置")

    try:
        async with AsyncClient() as client:
            # 腾讯地图API - 关键词搜索
            url = "https://apis.map.qq.com/ws/place/v1/search"

            params = {
                "key": settings.TENCENT_MAP_KEY,
                "keyword": keyword,
                "page_size": 20,
            }

            # 添加城市/区域筛选
            if city:
                params["boundary"] = f"region({city},0)"
            elif region:
                params["boundary"] = f"region({region},0)"

            response = await client.get(url, params=params, timeout=10.0)
            response.raise_for_status()
            data = response.json()

            if data.get("status") != 0:
                raise HTTPException(
                    status_code=400,
                    detail=f"地图搜索失败: {data.get('message', '未知错误')}"
                )

            # 解析返回结果
            locations = []
            for item in data.get("data", []):
                location = item.get("location", {})
                locations.append({
                    "id": item.get("id"),
                    "title": item.get("title"),
                    "address": item.get("address"),
                    "category": item.get("category"),
                    "latitude": location.get("lat"),
                    "longitude": location.get("lng"),
                    "ad_info": {
                        "province": item.get("ad_info", {}).get("province"),
                        "city": item.get("ad_info", {}).get("city"),
                        "district": item.get("ad_info", {}).get("district"),
                    }
                })

            return {
                "status": 0,
                "message": "success",
                "data": locations
            }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"搜索位置失败: {str(e)}")


@router.get("/geocode", summary="地址解析为坐标")
async def geocode(
    address: str = Query(..., description="地址"),
    city: Optional[str] = Query(None, description="城市"),
):
    """
    将地址转换为经纬度坐标

    参数:
    - address: 详细地址
    - city: 所在城市

    返回经纬度坐标
    """
    if not settings.TENCENT_MAP_KEY:
        raise HTTPException(status_code=400, detail="未配置腾讯地图Key")

    try:
        async with AsyncClient() as client:
            # 腾讯地图API - 地址解析
            url = "https://apis.map.qq.com/ws/geocoder/v1/"

            params = {
                "key": settings.TENCENT_MAP_KEY,
                "address": address,
            }

            if city:
                params["city"] = city

            response = await client.get(url, params=params, timeout=10.0)
            response.raise_for_status()
            data = response.json()

            if data.get("status") != 0:
                raise HTTPException(
                    status_code=400,
                    detail=f"地址解析失败: {data.get('message', '未知错误')}"
                )

            result = data.get("result", {})
            location = result.get("location", {})

            return {
                "status": 0,
                "message": "success",
                "data": {
                    "latitude": location.get("lat"),
                    "longitude": location.get("lng"),
                    "formatted_address": result.get("formatted_address"),
                    "address_components": result.get("address_component", {})
                }
            }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"地址解析失败: {str(e)}")
