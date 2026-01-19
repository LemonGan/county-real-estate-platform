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
    city: Optional[str] = Query(None, description="限定城市，如'杭州'"),
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
        # 开发环境返回模拟数据
        return _get_mock_locations(keyword)

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


def _get_mock_locations(keyword: str):
    """
    开发环境返回模拟数据
    """
    # 模拟杭州地区的一些位置
    mock_data = [
        {
            "id": "mock_1",
            "title": f"{keyword}（示例）",
            "address": "浙江省杭州市上城区",
            "category": "住宅区",
            "latitude": 30.287,
            "longitude": 120.153,
            "ad_info": {"province": "浙江省", "city": "杭州市", "district": "上城区"}
        },
        {
            "id": "mock_2",
            "title": "西湖景区",
            "address": "浙江省杭州市西湖区",
            "category": "旅游景点",
            "latitude": 30.259,
            "longitude": 120.131,
            "ad_info": {"province": "浙江省", "city": "杭州市", "district": "西湖区"}
        },
        {
            "id": "mock_3",
            "title": "钱江新城",
            "address": "浙江省杭州市上城区",
            "category": "商业区",
            "latitude": 30.275,
            "longitude": 120.185,
            "ad_info": {"province": "浙江省", "city": "杭州市", "district": "上城区"}
        },
        {
            "id": "mock_4",
            "title": "滨江高新区",
            "address": "浙江省杭州市滨江区",
            "category": "科技园区",
            "latitude": 30.208,
            "longitude": 120.212,
            "ad_info": {"province": "浙江省", "city": "杭州市", "district": "滨江区"}
        },
    ]

    return {
        "status": 0,
        "message": "success",
        "data": mock_data
    }
