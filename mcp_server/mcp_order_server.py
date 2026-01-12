# -*- coding: utf-8 -*-
"""
订票 MCP 服务器
==============
基于 FastMCP 提供票务预定接口（模拟）。

使用方式:
    python mcp_server/mcp_order_server.py

端口: 8003
"""

import logging
from mcp.server.fastmcp import FastMCP

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))
from config import settings

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def create_order_mcp_server():
    """创建并启动订票 MCP 服务器"""
    
    # 创建 FastMCP 实例
    order_mcp = FastMCP(
        name="OrderTools",
        instructions="票务预定工具，通过调用 API 完成火车票、飞机票和演唱会票的预定。",
        host="127.0.0.1",
        port=8003
    )
    
    @order_mcp.tool(
        name="order_train",
        description="根据时间、车次、座位类型、数量预定火车票"
    )
    def order_train(departure_date: str, train_number: str, seat_type: str, number: int) -> str:
        """
        预定火车票
        
        Args:
            departure_date: 出发日期，如 '2026-01-12'
            train_number: 火车车次，如 'G1'
            seat_type: 座位类型，如 '二等座'
            number: 订购张数
        """
        logger.info(f"正在订购火车票: {departure_date}, {train_number}, {seat_type}, {number}张")
        logger.info("恭喜，火车票预定成功！")
        return f"恭喜，火车票预定成功！{departure_date} {train_number} {seat_type} {number}张"
    
    @order_mcp.tool(
        name="order_flight",
        description="根据时间、航班号、舱位类型、数量预定飞机票"
    )
    def order_flight(departure_date: str, flight_number: str, cabin_type: str, number: int) -> str:
        """
        预定飞机票
        
        Args:
            departure_date: 出发日期，如 '2026-01-12'
            flight_number: 航班号，如 'CA1234'
            cabin_type: 舱位类型，如 '经济舱'
            number: 订购张数
        """
        logger.info(f"正在订购飞机票: {departure_date}, {flight_number}, {cabin_type}, {number}张")
        logger.info("恭喜，飞机票预定成功！")
        return f"恭喜，飞机票预定成功！{departure_date} {flight_number} {cabin_type} {number}张"
    
    @order_mcp.tool(
        name="order_concert",
        description="根据时间、明星、场地、座位类型、数量预定演出票"
    )
    def order_concert(start_date: str, artist: str, venue: str, ticket_type: str, number: int) -> str:
        """
        预定演出票
        
        Args:
            start_date: 演出日期，如 '2026-01-12'
            artist: 明星名称，如 '周杰伦'
            venue: 场地名称，如 '上海体育馆'
            ticket_type: 票类型，如 'VIP'
            number: 订购张数
        """
        logger.info(f"正在订购演出票: {start_date}, {artist}, {venue}, {ticket_type}, {number}张")
        logger.info("恭喜，演出票预定成功！")
        return f"恭喜，演出票预定成功！{start_date} {artist} @ {venue} {ticket_type} {number}张"
    
    # 打印服务器信息
    logger.info("=== 订票 MCP 服务器信息 ===")
    logger.info(f"名称: {order_mcp.name}")
    logger.info(f"端口: 8003")
    
    # 运行服务器
    try:
        print("订票 MCP 服务器已启动: http://127.0.0.1:8003/mcp")
        order_mcp.run(transport="streamable-http")
    except Exception as e:
        print(f"服务器启动失败: {e}")


if __name__ == "__main__":
    create_order_mcp_server()
