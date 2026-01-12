# -*- coding: utf-8 -*-
"""
定时任务调度模块
================
使用 schedule 库实现天气数据的定时更新。

知识点：
--------
1. schedule 是一个轻量级的 Python 定时任务库
2. 可以设置每天、每小时、每分钟等不同频率的任务
3. 使用 threading 可以让定时任务在后台运行，不阻塞主程序
4. 生产环境中，更推荐使用 APScheduler 或 Celery
"""

import time
import logging
import threading
from datetime import datetime

import schedule

from .weather_crawler import WeatherCrawler

# 配置日志
logger = logging.getLogger(__name__)


class WeatherScheduler:
    """
    天气数据定时更新器
    
    每天定时更新热门城市的天气数据。
    """
    
    def __init__(self):
        """初始化调度器"""
        self.crawler = WeatherCrawler()
        self._stop_event = threading.Event()
        self._thread = None
    
    def update_weather_job(self) -> None:
        """
        定时任务：更新天气数据
        
        这个方法会被 schedule 库定时调用。
        """
        logger.info(f"[{datetime.now()}] 开始更新天气数据...")
        
        try:
            results = self.crawler.update_hot_cities()
            for city, count in results.items():
                logger.info(f"  - {city}: 更新了 {count} 条记录")
            logger.info("天气数据更新完成！")
        except Exception as e:
            logger.error(f"天气数据更新失败: {e}")
    
    def start(self, update_time: str = "06:00") -> None:
        """
        启动定时任务
        
        Args:
            update_time: 每天更新时间，格式 HH:MM，默认早上 6 点
        
        知识点：
        --------
        schedule 库的常用方法：
        - schedule.every().day.at("06:00").do(job): 每天 6 点执行
        - schedule.every(10).minutes.do(job): 每 10 分钟执行
        - schedule.every().hour.do(job): 每小时执行
        - schedule.run_pending(): 运行所有到期的任务
        """
        # 设置每天定时任务
        schedule.every().day.at(update_time).do(self.update_weather_job)
        
        # 立即执行一次更新
        logger.info("立即执行首次天气数据更新...")
        self.update_weather_job()
        
        # 在后台线程中运行调度器
        def run_scheduler():
            logger.info(f"定时任务调度器已启动，每天 {update_time} 更新天气数据")
            while not self._stop_event.is_set():
                schedule.run_pending()
                time.sleep(60)  # 每分钟检查一次是否有任务需要执行
        
        self._thread = threading.Thread(target=run_scheduler, daemon=True)
        self._thread.start()
        logger.info("天气数据定时更新任务已在后台运行")
    
    def stop(self) -> None:
        """停止定时任务"""
        self._stop_event.set()
        if self._thread:
            self._thread.join(timeout=5)
        schedule.clear()
        logger.info("定时任务调度器已停止")


if __name__ == "__main__":
    import colorlog
    
    # 配置彩色日志
    handler = colorlog.StreamHandler()
    handler.setFormatter(colorlog.ColoredFormatter(
        '%(log_color)s%(asctime)s - %(levelname)s - %(message)s'
    ))
    logging.getLogger().addHandler(handler)
    logging.getLogger().setLevel(logging.INFO)
    
    print("=" * 50)
    print("测试定时任务调度器")
    print("=" * 50)
    
    scheduler = WeatherScheduler()
    
    # 启动调度器（会立即执行一次更新）
    scheduler.start("06:00")
    
    print("\n调度器已启动，按 Ctrl+C 停止...")
    
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        scheduler.stop()
        print("\n调度器已停止")
