# -*- coding: utf-8 -*-
"""
天气爬虫模块
============
从和风天气 API 获取天气预报数据并存入数据库。

知识点：
--------
1. requests 库用于发送 HTTP 请求
2. API 认证：将 API Key 放在请求参数中
3. JSON 解析：使用 response.json() 解析响应
4. 异常处理：网络请求可能失败，需要捕获异常
5. UPSERT：INSERT ... ON DUPLICATE KEY UPDATE 实现"有则更新，无则插入"
"""

import logging
from typing import List, Dict, Any, Optional
from datetime import datetime

import requests
from requests.exceptions import RequestException

# 导入配置和数据库
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))
from config import settings
from database import DatabaseConnection

# 配置日志
logger = logging.getLogger(__name__)


class WeatherCrawler:
    """
    和风天气 API 爬虫
    
    获取城市的 7 日天气预报数据。
    
    知识点：
    --------
    和风天气 API 文档：https://dev.qweather.com/docs/api/
    免费订阅限制：
    - 每天 1000 次调用
    - 只能使用 devapi.qweather.com
    - 只能获取国内城市数据
    """
    
    def __init__(self):
        """初始化爬虫"""
        self.api_key = settings.qweather_api_key
        self.base_url = settings.qweather_base_url
        
        if not self.api_key:
            logger.warning("和风天气 API Key 未配置，请检查 .env 文件")
    
    def get_city_code(self, city_name: str) -> Optional[str]:
        """
        查询城市代码
        
        Args:
            city_name: 城市名称（如"北京"）
        
        Returns:
            城市代码（Location ID），如果未找到返回 None
        
        知识点：
        --------
        和风天气使用 Location ID 标识城市，
        可以通过城市搜索 API 获取，也可以使用预置的城市代码表。
        """
        # 先从数据库查询
        try:
            results = DatabaseConnection.execute_query(
                "SELECT city_code FROM city_code WHERE city_name = %s",
                (city_name,)
            )
            if results:
                return results[0]["city_code"]
        except Exception as e:
            logger.error(f"查询城市代码失败: {e}")
        
        # 如果数据库中没有，调用 API 搜索
        return self._search_city_code(city_name)
    
    def _search_city_code(self, city_name: str) -> Optional[str]:
        """
        调用和风天气城市搜索 API
        
        Args:
            city_name: 城市名称
        
        Returns:
            城市代码
        """
        url = "https://geoapi.qweather.com/v2/city/lookup"
        params = {
            "location": city_name,
            "key": self.api_key,
            "number": 1  # 只返回第一个结果
        }
        
        try:
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()  # 如果状态码不是 2xx，抛出异常
            
            data = response.json()
            if data.get("code") == "200" and data.get("location"):
                city_info = data["location"][0]
                city_code = city_info["id"]
                
                # 保存到数据库以便下次使用
                self._save_city_code(city_name, city_code, city_info.get("adm1", ""))
                
                return city_code
            else:
                logger.warning(f"未找到城市: {city_name}")
                return None
                
        except RequestException as e:
            logger.error(f"城市搜索 API 请求失败: {e}")
            return None
    
    def _save_city_code(self, city_name: str, city_code: str, province: str) -> None:
        """保存城市代码到数据库"""
        try:
            DatabaseConnection.execute_update(
                """
                INSERT INTO city_code (city_name, city_code, province)
                VALUES (%s, %s, %s)
                ON DUPLICATE KEY UPDATE city_code = VALUES(city_code), province = VALUES(province)
                """,
                (city_name, city_code, province)
            )
        except Exception as e:
            logger.error(f"保存城市代码失败: {e}")
    
    def fetch_weather(self, city_name: str) -> Optional[List[Dict[str, Any]]]:
        """
        获取城市 7 日天气预报
        
        Args:
            city_name: 城市名称
        
        Returns:
            天气数据列表，如果失败返回 None
            
        知识点：
        --------
        和风天气 API 支持两种认证方式：
        1. JWT Bearer Token（推荐）: Authorization: Bearer <token>
        2. 传统 key 参数: ?key=<api_key>
        
        如果 403 错误，可能需要检查 API Key 是否激活。
        """
        city_code = self.get_city_code(city_name)
        if not city_code:
            logger.error(f"无法获取城市代码: {city_name}")
            return None
        
        # 使用 3 天预报（免费版支持）
        url = f"{self.base_url}/weather/3d"
        
        # 请求头（Bearer Token 认证）
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Accept-Encoding": "gzip"
        }
        
        # 查询参数
        params = {
            "location": city_code,
        }
        
        try:
            logger.info(f"正在获取 {city_name} 的天气预报...")
            
            # 首先尝试 Bearer Token 认证
            response = requests.get(url, headers=headers, params=params, timeout=10)
            
            # 如果 Bearer Token 失败，尝试传统 key 参数方式
            if response.status_code == 401 or response.status_code == 403:
                logger.warning("Bearer Token 认证失败，尝试 key 参数方式...")
                params["key"] = self.api_key
                response = requests.get(url, params=params, timeout=10)
            
            response.raise_for_status()
            
            data = response.json()
            if data.get("code") == "200" and data.get("daily"):
                weather_list = []
                for day in data["daily"]:
                    weather_list.append({
                        "city": city_name,
                        "city_code": city_code,
                        "fx_date": day["fxDate"],
                        "temp_max": int(day.get("tempMax", 0)),
                        "temp_min": int(day.get("tempMin", 0)),
                        "text_day": day.get("textDay", ""),
                        "text_night": day.get("textNight", ""),
                        "icon_day": day.get("iconDay", ""),
                        "icon_night": day.get("iconNight", ""),
                        "wind_dir_day": day.get("windDirDay", ""),
                        "wind_scale_day": day.get("windScaleDay", ""),
                        "wind_dir_night": day.get("windDirNight", ""),
                        "wind_scale_night": day.get("windScaleNight", ""),
                        "humidity": int(day.get("humidity", 0)),
                        "precip": float(day.get("precip", 0)),
                        "uv_index": int(day.get("uvIndex", 0)),
                        "vis": int(day.get("vis", 0)),
                    })
                
                logger.info(f"成功获取 {city_name} 的 {len(weather_list)} 天天气预报")
                return weather_list
            else:
                error_code = data.get("code", "unknown")
                logger.error(f"API 返回错误码: {error_code}")
                if error_code == "401":
                    logger.error("认证失败，请检查 API Key 是否正确")
                elif error_code == "403":
                    logger.error("无权访问，请检查 API Key 是否已激活或订阅是否有效")
                return None
                
        except RequestException as e:
            logger.error(f"天气 API 请求失败: {e}")
            return None
    
    def save_weather_to_db(self, weather_list: List[Dict[str, Any]]) -> int:
        """
        将天气数据保存到数据库
        
        Args:
            weather_list: 天气数据列表
        
        Returns:
            成功保存的记录数
            
        知识点：
        --------
        ON DUPLICATE KEY UPDATE 语法：
        当插入的数据违反唯一约束时，转为更新操作。
        这样可以保证同一城市同一日期只有一条记录，且始终是最新数据。
        """
        if not weather_list:
            return 0
        
        sql = """
        INSERT INTO weather_data (
            city, city_code, fx_date, temp_max, temp_min,
            text_day, text_night, icon_day, icon_night,
            wind_dir_day, wind_scale_day, wind_dir_night, wind_scale_night,
            humidity, precip, uv_index, vis
        ) VALUES (
            %(city)s, %(city_code)s, %(fx_date)s, %(temp_max)s, %(temp_min)s,
            %(text_day)s, %(text_night)s, %(icon_day)s, %(icon_night)s,
            %(wind_dir_day)s, %(wind_scale_day)s, %(wind_dir_night)s, %(wind_scale_night)s,
            %(humidity)s, %(precip)s, %(uv_index)s, %(vis)s
        )
        ON DUPLICATE KEY UPDATE
            temp_max = VALUES(temp_max),
            temp_min = VALUES(temp_min),
            text_day = VALUES(text_day),
            text_night = VALUES(text_night),
            icon_day = VALUES(icon_day),
            icon_night = VALUES(icon_night),
            wind_dir_day = VALUES(wind_dir_day),
            wind_scale_day = VALUES(wind_scale_day),
            wind_dir_night = VALUES(wind_dir_night),
            wind_scale_night = VALUES(wind_scale_night),
            humidity = VALUES(humidity),
            precip = VALUES(precip),
            uv_index = VALUES(uv_index),
            vis = VALUES(vis),
            updated_at = CURRENT_TIMESTAMP
        """
        
        saved_count = 0
        for weather in weather_list:
            try:
                # 使用命名参数需要特殊处理
                from database.connection import DatabaseConnection as DB
                with DB.get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute(sql, weather)
                    conn.commit()
                    saved_count += 1
                    cursor.close()
            except Exception as e:
                logger.error(f"保存天气数据失败: {e}")
        
        logger.info(f"成功保存 {saved_count} 条天气记录")
        return saved_count
    
    def update_hot_cities(self) -> Dict[str, int]:
        """
        更新热门城市的天气数据
        
        返回：
            Dict[str, int]: 城市名称 -> 保存记录数
        """
        hot_cities = ["北京", "上海", "广州", "深圳"]
        results = {}
        
        for city in hot_cities:
            weather_list = self.fetch_weather(city)
            if weather_list:
                count = self.save_weather_to_db(weather_list)
                results[city] = count
            else:
                results[city] = 0
        
        return results


if __name__ == "__main__":
    # 测试天气爬虫
    import colorlog
    
    # 配置彩色日志
    handler = colorlog.StreamHandler()
    handler.setFormatter(colorlog.ColoredFormatter(
        '%(log_color)s%(asctime)s - %(levelname)s - %(message)s'
    ))
    logging.getLogger().addHandler(handler)
    logging.getLogger().setLevel(logging.INFO)
    
    print("=" * 50)
    print("测试天气爬虫")
    print("=" * 50)
    
    crawler = WeatherCrawler()
    
    # 测试获取单个城市天气
    weather = crawler.fetch_weather("北京")
    if weather:
        print(f"\n北京未来 7 天天气：")
        for day in weather[:3]:  # 只显示前 3 天
            print(f"  {day['fx_date']}: {day['text_day']}, {day['temp_min']}~{day['temp_max']}°C")
        
        # 保存到数据库
        count = crawler.save_weather_to_db(weather)
        print(f"\n已保存 {count} 条记录到数据库")
    
    print("=" * 50)
