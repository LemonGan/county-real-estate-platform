#!/usr/bin/env python3
"""房源批量导入脚本 - 独立版"""
import csv
import json
import sys
import os

import pymysql
from pymysql import cursors

# 数据库配置
DB_CONFIG = {
    'host': 'localhost',
    'user': 'root',
    'password': 'gjl421911',
    'database': 'xqfc_db',
    'charset': 'utf8mb4',
    'cursorclass': cursors.DictCursor
}

def generate_property_no(index):
    """生成房源编号 - 使用不同的编号避免重复"""
    return f"REAL{index+1:04d}"

def import_properties(csv_path):
    """从CSV导入房源数据"""
    conn = pymysql.connect(**DB_CONFIG)
    
    count = 0
    errors = []
    
    try:
        with conn.cursor() as cursor:
            with open(csv_path, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                
                for row in reader:
                    try:
                        # 处理标签 - 转为JSON数组
                        tags = row.get('tags', '')
                        tags_list = [t.strip() for t in tags.split(',') if t.strip()]
                        tags_json = json.dumps(tags_list, ensure_ascii=False)
                        
                        sql = """
                        INSERT INTO properties (
                            title, description, property_type, transaction_type,
                            province, city, district, town, detail_address,
                            total_price, unit_price, area,
                            room_count, hall_count, bathroom_count,
                            floor_info, total_floors, build_year, decoration_type,
                            cover_image_url, tags,
                            contact_phone, contact_name,
                            agent_id, status, property_no
                        ) VALUES (
                            %s, %s, %s, %s, %s, %s, %s, %s, %s,
                            %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
                            %s, %s, %s, %s, %s, %s, %s
                        )
                        """
                        
                        values = (
                            row['title'],
                            row.get('description', ''),
                            int(row['property_type']),
                            int(row['transaction_type']),
                            row['province'],
                            row['city'],
                            row['district'],
                            row.get('town', ''),
                            row.get('detail_address', ''),
                            int(row['total_price']),
                            int(row['unit_price']),
                            float(row['area']),
                            int(row['room_count']) if row.get('room_count') else None,
                            int(row['hall_count']) if row.get('hall_count') else None,
                            int(row['bathroom_count']) if row.get('bathroom_count') else None,
                            row.get('floor_info', ''),
                            int(row['total_floors']) if row.get('total_floors') else None,
                            int(row['build_year']) if row.get('build_year') else None,
                            int(row['decoration_type']) if row.get('decoration_type') else None,
                            row.get('cover_image_url', ''),
                            tags_json,
                            row.get('contact_phone', ''),
                            row.get('contact_name', ''),
                            1,  # 默认经纪人ID
                            1,  # 在售状态
                            generate_property_no(count)
                        )
                        
                        cursor.execute(sql, values)
                        count += 1
                        print(f"[OK] {count}: {row['title']}")
                        
                    except Exception as e:
                        errors.append(f"第{count+1}行: {str(e)}")
                        print(f"[FAIL] 第{count+1}行: {e}")
        
        conn.commit()
        print(f"\n{'='*50}")
        print(f"[OK] 成功导入 {count} 条房源")
        if errors:
            print(f"[FAIL] 失败 {len(errors)} 条")
            for e in errors:
                print(f"   - {e}")
        print(f"{'='*50}")
        
    finally:
        conn.close()

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("用法: python import_properties.py <csv文件路径>")
        sys.exit(1)
    
    csv_path = sys.argv[1]
    if not os.path.exists(csv_path):
        print(f"❌ 文件不存在: {csv_path}")
        sys.exit(1)
    
    import_properties(csv_path)
