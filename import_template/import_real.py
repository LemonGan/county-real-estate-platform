#!/usr/bin/env python3
"""导入真实房源数据"""
import json
import pymysql
from pymysql import cursors

DB_CONFIG = {
    'host': 'localhost',
    'user': 'root',
    'password': 'gjl421911',
    'database': 'xqfc_db',
    'charset': 'utf8mb4',
    'cursorclass': cursors.DictCursor
}

def generate_property_no(index):
    return f'REAL{index+1:04d}'

properties = [
    {'title': '湘桂盛世名城二期电梯房出售', 'description': '湘桂盛世名城二期，电梯房，4室2厅2卫，新净明亮，128平米，52万', 'property_type': 1, 'transaction_type': 1, 'province': '广西', 'city': '钦州市', 'district': '灵山县', 'town': '灵城镇', 'detail_address': '湘桂盛世名城', 'total_price': 520000, 'unit_price': 4063, 'area': 128, 'room_count': 4, 'hall_count': 2, 'bathroom_count': 2, 'floor_info': '中高层', 'total_floors': 26, 'build_year': 2020, 'decoration_type': 2, 'cover_image_url': '', 'tags': '电梯房,学区房', 'contact_phone': '', 'contact_name': ''},
    {'title': '金色家园文峰路75号出售', 'description': '金色家园，灵山城区文峰路75号，总价低，单价3650元/平', 'property_type': 1, 'transaction_type': 1, 'province': '广西', 'city': '钦州市', 'district': '灵山县', 'town': '灵城镇', 'detail_address': '金色家园', 'total_price': 0, 'unit_price': 3650, 'area': 100, 'room_count': 3, 'hall_count': 2, 'bathroom_count': 1, 'floor_info': '中层', 'total_floors': 7, 'build_year': 2015, 'decoration_type': 2, 'cover_image_url': '', 'tags': '低价,配套成熟', 'contact_phone': '', 'contact_name': ''},
    {'title': '江景豪庭丰裕路130号出售', 'description': '江景豪庭，灵山城区丰裕路130号，2套在售，单价3050元/平', 'property_type': 1, 'transaction_type': 1, 'province': '广西', 'city': '钦州市', 'district': '灵山县', 'town': '灵城镇', 'detail_address': '江景豪庭', 'total_price': 0, 'unit_price': 3050, 'area': 100, 'room_count': 3, 'hall_count': 2, 'bathroom_count': 1, 'floor_info': '中层', 'total_floors': 7, 'build_year': 2016, 'decoration_type': 2, 'cover_image_url': '', 'tags': '江景房,低价', 'contact_phone': '', 'contact_name': ''},
    {'title': '灵山碧桂园小区出售', 'description': '灵山碧桂园，湘桂大道延长线(气象局东南面)，2019年竣工，占地90869.5平，70年产权，11套房源', 'property_type': 1, 'transaction_type': 1, 'province': '广西', 'city': '钦州市', 'district': '灵山县', 'town': '灵城镇', 'detail_address': '灵山碧桂园', 'total_price': 0, 'unit_price': 0, 'area': 100, 'room_count': 4, 'hall_count': 2, 'bathroom_count': 2, 'floor_info': '高层', 'total_floors': 30, 'build_year': 2019, 'decoration_type': 2, 'cover_image_url': '', 'tags': '品牌开发商,电梯房', 'contact_phone': '', 'contact_name': ''},
]

conn = pymysql.connect(**DB_CONFIG)
count = 0

with conn.cursor() as cursor:
    for i, row in enumerate(properties):
        tags_json = json.dumps(row['tags'].split(','), ensure_ascii=False)
        sql = '''INSERT INTO properties (title, description, property_type, transaction_type, province, city, district, town, detail_address, total_price, unit_price, area, room_count, hall_count, bathroom_count, floor_info, total_floors, build_year, decoration_type, cover_image_url, tags, contact_phone, contact_name, agent_id, status, property_no) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)'''
        values = (row['title'], row['description'], row['property_type'], row['transaction_type'], row['province'], row['city'], row['district'], row['town'], row['detail_address'], row['total_price'], row['unit_price'], row['area'], row['room_count'], row['hall_count'], row['bathroom_count'], row['floor_info'], row['total_floors'], row['build_year'], row['decoration_type'], row['cover_image_url'], tags_json, row['contact_phone'], row['contact_name'], 1, 1, generate_property_no(i))
        cursor.execute(sql, values)
        count += 1
        print(f'[OK] {count}: {row["title"]}')

conn.commit()
conn.close()
print(f'Total: {count} properties imported')
