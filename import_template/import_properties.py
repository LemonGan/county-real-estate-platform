#!/usr/bin/env python3
"""
房源批量导入脚本
用法: python import_properties.py <csv文件路径>
"""
import csv
import sys
import os

# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.models.property import Property
from app.core.database import Base
import asyncio


def get_engine():
    """创建数据库引擎"""
    DATABASE_URL = "mysql+asyncmy://xqfc_db:Lemon421911*@localhost:3306/xqfc_db?charset=utf8mb4"
    # 同步版本用于导入
    sync_url = "mysql+pymysql://xqfc_db:Lemon421911*@localhost:3306/xqfc_db?charset=utf8mb4"
    return create_engine(sync_url, pool_pre_ping=True)


def import_properties(csv_path):
    """从CSV导入房源数据"""
    engine = get_engine()
    
    # 确保表存在
    Base.metadata.create_all(engine)
    
    Session = sessionmaker(bind=engine)
    session = Session()
    
    count = 0
    errors = []
    
    with open(csv_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        
        for row in reader:
            try:
                property = Property(
                    title=row['title'],
                    description=row.get('description', ''),
                    property_type=int(row['property_type']),
                    transaction_type=int(row['transaction_type']),
                    province=row['province'],
                    city=row['city'],
                    district=row['district'],
                    town=row.get('town', ''),
                    detail_address=row.get('detail_address', ''),
                    total_price=int(row['total_price']),
                    unit_price=int(row['unit_price']),
                    area=float(row['area']),
                    room_count=int(row['room_count']) if row.get('room_count') else None,
                    hall_count=int(row['hall_count']) if row.get('hall_count') else None,
                    bathroom_count=int(row['bathroom_count']) if row.get('bathroom_count') else None,
                    floor_info=row.get('floor_info', ''),
                    total_floors=int(row['total_floors']) if row.get('total_floors') else None,
                    build_year=int(row['build_year']) if row.get('build_year') else None,
                    decoration_type=int(row['decoration_type']) if row.get('decoration_type') else None,
                    cover_image_url=row.get('cover_image_url', ''),
                    tags=row.get('tags', '').split(',') if row.get('tags') else [],
                    contact_phone=row.get('contact_phone', ''),
                    contact_name=row.get('contact_name', ''),
                    agent_id=1,  # 默认经纪人ID
                    status=1,  # 在售
                    property_no=f"LS{count+1:04d}"  # 生成编号
                )
                session.add(property)
                count += 1
                
            except Exception as e:
                errors.append(f"第{count+1}行导入失败: {str(e)}")
    
    session.commit()
    session.close()
    
    print(f"✅ 成功导入 {count} 条房源")
    if errors:
        print(f"❌ 失败 {len(errors)} 条:")
        for e in errors:
            print(f"   - {e}")
    return count


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("用法: python import_properties.py <csv文件路径>")
        sys.exit(1)
    
    csv_path = sys.argv[1]
    if not os.path.exists(csv_path):
        print(f"❌ 文件不存在: {csv_path}")
        sys.exit(1)
    
    import_properties(csv_path)
