import pymysql
import json

conn = pymysql.connect(host='8.138.129.142', port=3306, user='xqfc_db', password='Lemon421911*', database='xqfc_db', charset='utf8mb4')
cursor = conn.cursor()

# 先清空
cursor.execute('DELETE FROM properties')

# 插入4条真实房源
properties = [
    ("REAL001", 21, "湘桂盛世名城二期电梯房出售", "湘桂盛世名城二期，电梯房，4室2厅2卫，新净明亮，128平米，52万", 1, 1, "广西", "钦州市", "灵山县", "灵城镇", "湘桂盛世名城", 520000, 4063, 128.00, 4, 2, 2, "中高层", 26, 2020, 2, 1, 1, 1, 0, 0, 0, '["电梯房", "学区房"]', "湘桂盛世名城 灵山 电梯房", "13800138001", "张经理"),
    ("REAL002", 21, "金色家园文峰路75号出售", "金色家园，灵山城区文峰路75号，总价低，单价3650元/平", 1, 1, "广西", "钦州市", "灵山县", "灵城镇", "金色家园", 365000, 3650, 100.00, 3, 2, 1, "中层", 7, 2015, 2, 1, 1, 1, 0, 0, 0, '["低价", "配套成熟"]', "金色家园 灵山 二手房", "13800138002", "李经理"),
    ("REAL003", 21, "江景豪庭丰裕路130号出售", "江景豪庭，灵山城区丰裕路130号，2套在售，单价3050元/平", 1, 1, "广西", "钦州市", "灵山县", "灵城镇", "江景豪庭", 305000, 3050, 100.00, 3, 2, 1, "中层", 7, 2016, 2, 1, 1, 1, 0, 0, 0, '["江景房", "低价"]', "江景豪庭 灵山 二手房", "13800138003", "王经理"),
    ("REAL004", 21, "灵山碧桂园小区出售", "灵山碧桂园，湘桂大道延长线，2019年竣工，占地90869.5平，70年产权，11套房源", 1, 1, "广西", "钦州市", "灵山县", "灵城镇", "灵山碧桂园", 800000, 5500, 145.00, 4, 2, 2, "高层", 30, 2019, 2, 1, 1, 1, 0, 0, 0, '["品牌开发商", "电梯房"]', "灵山碧桂园 灵山 新房", "13800138004", "陈经理"),
]

sql = '''INSERT INTO properties (property_no, agent_id, title, description, property_type, transaction_type, province, city, district, town, detail_address, total_price, unit_price, area, room_count, hall_count, bathroom_count, floor_info, total_floors, build_year, decoration_type, status, audit_status, verify_status, view_count, favorite_count, inquiry_count, tags, keywords, contact_phone, contact_name) VALUES '''

for i, p in enumerate(properties):
    if i > 0:
        sql += ", "
    sql += f"('{p[0]}', {p[1]}, '{p[2]}', '{p[3]}', {p[4]}, {p[5]}, '{p[6]}', '{p[7]}', '{p[8]}', '{p[9]}', '{p[10]}', {p[11]}, {p[12]}, {p[13]}, {p[14]}, {p[15]}, {p[16]}, '{p[17]}', {p[18]}, {p[19]}, {p[20]}, {p[21]}, {p[22]}, {p[23]}, {p[24]}, {p[25]}, {p[26]}, '{p[27]}', '{p[28]}', '{p[29]}', '{p[30]}')"

cursor.execute(sql)
conn.commit()

cursor.execute('SELECT id, title, total_price FROM properties')
print('Inserted:', cursor.fetchall())

conn.close()
print('Done!')
