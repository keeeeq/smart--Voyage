# -*- coding: utf-8 -*-
"""
插入测试数据脚本
"""

import mysql.connector
from datetime import date, timedelta
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from config import settings


def insert_test_data():
    """插入测试数据"""
    conn = mysql.connector.connect(
        host=settings.mysql_host,
        user=settings.mysql_user,
        password=settings.mysql_password,
        database=settings.mysql_database
    )
    cursor = conn.cursor()
    
    today = date.today()
    tomorrow = today + timedelta(days=1)
    
    print("开始插入测试数据...")
    
    # ============ 火车票数据 ============
    train_data = [
        # 北京-上海
        ('G1', '北京', '北京南站', '07:00:00', '上海', '上海虹桥', '11:36:00', today, '4h36m', 553.00, 933.00, 100, 50),
        ('G3', '北京', '北京南站', '08:00:00', '上海', '上海虹桥', '12:40:00', today, '4h40m', 553.00, 933.00, 80, 30),
        ('G5', '北京', '北京南站', '09:00:00', '上海', '上海虹桥', '13:28:00', today, '4h28m', 553.00, 933.00, 120, 60),
        # 上海-北京
        ('G2', '上海', '上海虹桥', '07:00:00', '北京', '北京南站', '11:30:00', today, '4h30m', 553.00, 933.00, 90, 40),
        ('G4', '上海', '上海虹桥', '08:00:00', '北京', '北京南站', '12:36:00', today, '4h36m', 553.00, 933.00, 100, 50),
        # 北京-杭州
        ('G31', '北京', '北京南站', '08:05:00', '杭州', '杭州东站', '13:23:00', today, '5h18m', 626.00, 1056.00, 80, 40),
        # 上海-杭州
        ('G7501', '上海', '上海虹桥', '07:00:00', '杭州', '杭州东站', '07:59:00', today, '59m', 73.00, 117.00, 200, 100),
        # 明天
        ('G1', '北京', '北京南站', '07:00:00', '上海', '上海虹桥', '11:36:00', tomorrow, '4h36m', 553.00, 933.00, 200, 100),
    ]
    
    train_sql = """
    INSERT INTO train_ticket 
    (train_no, from_city, from_station, departure_time, to_city, to_station, arrival_time, travel_date, duration, price_second, price_first, stock_second, stock_first) 
    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
    ON DUPLICATE KEY UPDATE stock_second = VALUES(stock_second), stock_first = VALUES(stock_first)
    """
    
    for data in train_data:
        try:
            cursor.execute(train_sql, data)
        except Exception as e:
            print(f"火车票插入失败: {e}")
    
    print(f"  ✓ 火车票: {len(train_data)} 条")
    
    # ============ 机票数据 ============
    flight_data = [
        ('CA1501', '中国国航', '北京', '首都T3', f'{today} 07:00:00', '上海', '虹桥T2', f'{today} 09:20:00', today, '2h20m', 1200.00, 3600.00, 0.8),
        ('MU5101', '东方航空', '北京', '大兴', f'{today} 08:00:00', '上海', '浦东T1', f'{today} 10:30:00', today, '2h30m', 1100.00, 3300.00, 0.7),
        ('CA1502', '中国国航', '上海', '虹桥T2', f'{today} 07:30:00', '北京', '首都T3', f'{today} 09:50:00', today, '2h20m', 1200.00, 3600.00, 0.8),
        ('CA1301', '中国国航', '北京', '首都T3', f'{today} 07:00:00', '广州', '白云T2', f'{today} 10:10:00', today, '3h10m', 1600.00, 4800.00, 0.65),
        ('MU5301', '东方航空', '上海', '浦东T1', f'{today} 08:00:00', '深圳', '宝安T3', f'{today} 10:30:00', today, '2h30m', 1300.00, 3900.00, 0.75),
    ]
    
    flight_sql = """
    INSERT INTO flight_ticket 
    (flight_no, airline, from_city, from_airport, departure_time, to_city, to_airport, arrival_time, flight_date, duration, price_economy, price_business, discount) 
    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
    ON DUPLICATE KEY UPDATE price_economy = VALUES(price_economy)
    """
    
    for data in flight_data:
        try:
            cursor.execute(flight_sql, data)
        except Exception as e:
            print(f"机票插入失败: {e}")
    
    print(f"  ✓ 机票: {len(flight_data)} 条")
    
    # ============ 演唱会数据 ============
    concert_data = [
        ('周杰伦演唱会-北京站', '周杰伦', '北京', '鸟巢', today + timedelta(days=30), '19:30:00', '预售', 380.00, 1880.00, '周杰伦巡回演唱会'),
        ('五月天演唱会-上海站', '五月天', '上海', '梅奔中心', today + timedelta(days=14), '19:00:00', '在售', 280.00, 1280.00, '五月天演唱会'),
        ('林俊杰演唱会-广州站', '林俊杰', '广州', '广州体育馆', today + timedelta(days=21), '19:30:00', '在售', 320.00, 1580.00, 'JJ演唱会'),
        ('薛之谦演唱会-杭州站', '薛之谦', '杭州', '黄龙中心', today + timedelta(days=7), '19:30:00', '在售', 280.00, 1280.00, '薛之谦巡演'),
    ]
    
    concert_sql = """
    INSERT INTO concert_ticket 
    (concert_name, artist, city, venue, show_date, show_time, status, price_min, price_max, description) 
    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
    ON DUPLICATE KEY UPDATE status = VALUES(status)
    """
    
    for data in concert_data:
        try:
            cursor.execute(concert_sql, data)
        except Exception as e:
            print(f"演唱会插入失败: {e}")
    
    print(f"  ✓ 演唱会: {len(concert_data)} 条")
    
    # ============ 天气数据 ============
    weather_data = [
        ('北京', '101010100', today, 5, -3, '晴', '晴', 35, '北风', 0.0, 4),
        ('北京', '101010100', tomorrow, 6, -2, '多云', '多云', 40, '东北风', 0.0, 3),
        ('上海', '101020100', today, 12, 5, '多云', '阴', 65, '东风', 0.0, 5),
        ('上海', '101020100', tomorrow, 14, 7, '晴', '晴', 55, '东南风', 0.0, 6),
        ('广州', '101280101', today, 22, 15, '晴', '晴', 60, '北风', 0.0, 7),
        ('深圳', '101280601', today, 23, 16, '多云', '多云', 65, '东北风', 0.0, 6),
        ('杭州', '101210101', today, 10, 3, '阴', '小雨', 70, '东风', 3.0, 3),
    ]
    
    weather_sql = """
    INSERT INTO weather_data 
    (city, city_code, fx_date, temp_max, temp_min, text_day, text_night, humidity, wind_dir_day, precip, uv_index) 
    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
    ON DUPLICATE KEY UPDATE temp_max = VALUES(temp_max), temp_min = VALUES(temp_min), text_day = VALUES(text_day)
    """
    
    for data in weather_data:
        try:
            cursor.execute(weather_sql, data)
        except Exception as e:
            print(f"天气插入失败: {e}")
    
    print(f"  ✓ 天气: {len(weather_data)} 条")
    
    conn.commit()
    cursor.close()
    conn.close()
    
    print("\n测试数据插入完成！")
    print(f"今天日期: {today}")


if __name__ == "__main__":
    insert_test_data()
