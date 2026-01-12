# -*- coding: utf-8 -*-
"""
票务 MCP 服务器
==============
基于 FastMCP 提供火车票、机票、演唱会票查询接口。

使用方式:
    python mcp_server/mcp_ticket_server.py

端口: 8001
"""

import json
import logging
from datetime import date, datetime, timedelta
from decimal import Decimal

import mysql.connector
from mcp.server.fastmcp import FastMCP

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))
from config import settings

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# JSON 编码器：处理特殊类型
def default_encoder(obj):
    """将 MySQL 特殊类型转换为 JSON 兼容格式"""
    if isinstance(obj, datetime):
        return obj.strftime('%Y-%m-%d %H:%M:%S')
    if isinstance(obj, date):
        return obj.strftime('%Y-%m-%d')
    if isinstance(obj, timedelta):
        return str(obj)
    if isinstance(obj, Decimal):
        return float(obj)
    return obj


class TicketService:
    """票务数据服务类"""
    
    def __init__(self):
        """初始化数据库连接"""
        self.db_config = {
            "host": settings.mysql_host,
            "user": settings.mysql_user,
            "password": settings.mysql_password,
            "database": settings.mysql_database
        }
        self.conn = None
        self._connect()
    
    def _connect(self):
        """建立数据库连接"""
        try:
            self.conn = mysql.connector.connect(**self.db_config)
            logger.info("票务服务数据库连接成功")
        except Exception as e:
            logger.error(f"数据库连接失败: {e}")
            self.conn = None
    
    def _ensure_connection(self):
        """确保数据库连接可用"""
        try:
            if self.conn is None or not self.conn.is_connected():
                logger.info("数据库连接已断开，正在重连...")
                self._connect()
        except Exception:
            self._connect()
    
    def execute_query(self, sql: str) -> str:
        """
        执行 SQL 查询
        
        Args:
            sql: SELECT 语句
        
        Returns:
            JSON 格式的查询结果
        """
        try:
            # 确保连接可用
            self._ensure_connection()
            
            if self.conn is None:
                return json.dumps(
                    {"status": "error", "message": "数据库连接失败"},
                    ensure_ascii=False
                )
            
            cursor = self.conn.cursor(dictionary=True)
            cursor.execute(sql)
            results = cursor.fetchall()
            cursor.close()
            
            # 格式化结果中的特殊类型
            for result in results:
                for key, value in result.items():
                    if isinstance(value, (date, datetime, timedelta, Decimal)):
                        result[key] = default_encoder(value)
            
            if results:
                return json.dumps(
                    {"status": "success", "data": results},
                    ensure_ascii=False
                )
            else:
                return json.dumps(
                    {"status": "no_data", "message": "未找到票务数据，请确认查询条件。"},
                    ensure_ascii=False
                )
        except Exception as e:
            logger.error(f"票务查询错误: {str(e)}")
            return json.dumps(
                {"status": "error", "message": str(e)},
                ensure_ascii=False
            )


def create_ticket_mcp_server():
    """创建并启动票务 MCP 服务器"""
    
    # 创建 FastMCP 实例
    ticket_mcp = FastMCP(
        name="TicketTools",
        instructions="票务查询工具，支持 train_ticket, flight_ticket, concert_ticket 表。",
        host="127.0.0.1",
        port=8001
    )
    
    # 初始化服务
    service = TicketService()
    
    @ticket_mcp.tool(
        name="query_tickets",
        description="查询票务数据，输入 SQL，如 'SELECT * FROM train_ticket WHERE from_city = \"北京\" AND to_city = \"上海\"'"
    )
    def query_tickets(sql: str) -> str:
        """执行票务查询"""
        logger.info(f"执行票务查询: {sql}")
        return service.execute_query(sql)
    
    # 打印服务器信息
    logger.info("=== 票务 MCP 服务器信息 ===")
    logger.info(f"名称: {ticket_mcp.name}")
    logger.info(f"端口: 8001")
    
    # 运行服务器
    try:
        print("票务 MCP 服务器已启动: http://127.0.0.1:8001/mcp")
        ticket_mcp.run(transport="streamable-http")
    except Exception as e:
        print(f"服务器启动失败: {e}")


if __name__ == "__main__":
    create_ticket_mcp_server()
