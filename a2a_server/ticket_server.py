# -*- coding: utf-8 -*-
"""
票务 A2A Agent 服务器
====================
使用 LLM 生成 SQL 查询票务 MCP 工具，返回用户友好文本结果。

使用方式:
    python a2a_server/ticket_server.py

端口: 5006
依赖: MCP票务服务器 (8001)
"""

import json
import asyncio
import logging
from datetime import datetime

import pytz
from mcp import ClientSession
from mcp.client.streamable_http import streamablehttp_client
from python_a2a import A2AServer, run_server, AgentCard, AgentSkill, TaskStatus, TaskState
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))
from config import settings

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 初始化 LLM
llm = ChatOpenAI(
    model=settings.openai_model,
    base_url=settings.openai_base_url,
    api_key=settings.openai_api_key,
    temperature=0.1
)

# SQL 生成提示词
SQL_PROMPT = ChatPromptTemplate.from_template("""
系统提示：你是一个专业的票务SQL生成器，根据用户意图生成 SELECT 语句。

## 数据库表结构

### train_ticket（火车票表）
- train_no: 车次号（如 G1）
- from_city: 出发城市
- from_station: 出发站
- to_city: 到达城市
- to_station: 到达站
- departure_time: 出发时间
- arrival_time: 到达时间
- travel_date: 乘车日期（DATE 类型）
- duration: 行程时长
- price_second: 二等座票价
- price_first: 一等座票价
- stock_second: 二等座余票
- stock_first: 一等座余票

### flight_ticket（机票表）
- flight_no: 航班号
- airline: 航空公司
- from_city: 出发城市
- from_airport: 出发机场
- to_city: 到达城市
- to_airport: 到达机场
- departure_time: 出发时间
- arrival_time: 到达时间
- flight_date: 航班日期（DATE 类型）
- duration: 飞行时长
- price_economy: 经济舱票价
- price_business: 商务舱票价

### concert_ticket（演唱会表）
- concert_name: 演唱会名称
- artist: 艺人名称
- city: 城市
- venue: 场馆
- show_date: 演出日期（DATE 类型，注意：不是 event_date）
- show_time: 演出时间
- status: 状态（预售/在售/售罄）
- price_min: 最低票价
- price_max: 最高票价

## 规则
1. 先输出类型 JSON：{{"type": "train/flight/concert"}}
2. 然后输出 SQL 语句
3. 查询未来演出：WHERE show_date >= '当前日期'
4. 信息不足时返回：{{"status": "input_required", "message": "追问内容"}}

## 示例
输入: 北京到上海的火车票
输出:
{{"type": "train"}}
SELECT * FROM train_ticket WHERE from_city = '北京' AND to_city = '上海' AND travel_date >= '{current_date}' ORDER BY departure_time LIMIT 10

输入: 上海有什么演唱会
输出:
{{"type": "concert"}}
SELECT * FROM concert_ticket WHERE city = '上海' AND show_date >= '{current_date}' ORDER BY show_date LIMIT 10

输入: 五月天演唱会
输出:
{{"type": "concert"}}
SELECT * FROM concert_ticket WHERE artist LIKE '%五月天%' AND show_date >= '{current_date}' ORDER BY show_date LIMIT 10

当前日期: {current_date}
对话历史: {conversation}
""")


async def get_tickets(sql: str) -> dict:
    """调用票务 MCP 服务器"""
    try:
        async with streamablehttp_client("http://127.0.0.1:8001/mcp") as (read, write, _):
            async with ClientSession(read, write) as session:
                await session.initialize()
                result = await session.call_tool("query_tickets", {"sql": sql})
                return result.content[0].text
    except Exception as e:
        logger.error(f"调用票务 MCP 失败: {e}")
        return json.dumps({"status": "error", "message": str(e)})


# Agent Card 定义
agent_card = AgentCard(
    name="TicketQueryAssistant",
    description="基于 LangChain 提供票务查询服务的助手",
    url="http://localhost:5006",
    version="1.0.0",
    capabilities={"streaming": True, "memory": True},
    skills=[
        AgentSkill(
            name="execute ticket query",
            description="执行票务查询（火车票、机票、演唱会票）",
            examples=["火车票 北京 上海 2026-01-12", "机票 北京 广州", "周杰伦演唱会"]
        )
    ]
)


class TicketQueryServer(A2AServer):
    """票务查询 A2A 服务器"""
    
    def __init__(self):
        super().__init__(agent_card=agent_card)
        self.llm = llm
        self.sql_prompt = SQL_PROMPT
    
    def generate_sql_query(self, conversation: str) -> dict:
        """生成 SQL 查询"""
        try:
            chain = self.sql_prompt | self.llm
            current_date = datetime.now(pytz.timezone('Asia/Shanghai')).strftime('%Y-%m-%d')
            output = chain.invoke({
                "conversation": conversation,
                "current_date": current_date
            }).content.strip()
            
            logger.info(f"LLM 输出: {output}")
            
            lines = output.strip().split('\n')
            type_line = lines[0].strip()
            
            if type_line.startswith('{"status":'):
                return json.loads(type_line)
            
            if type_line.startswith('{"type":'):
                query_type = json.loads(type_line)["type"]
                sql_query = ' '.join(lines[1:]).strip()
                return {"status": "sql", "type": query_type, "sql": sql_query}
            
            return {"status": "input_required", "message": "无法识别查询类型，请提供更多信息"}
        except Exception as e:
            logger.error(f"SQL 生成失败: {e}")
            return {"status": "input_required", "message": "查询无效，请提供票务相关信息"}
    
    def handle_task(self, task):
        """处理任务"""
        content = (task.message or {}).get("content", {})
        conversation = content.get("text", "") if isinstance(content, dict) else ""
        logger.info(f"收到查询: {conversation}")
        
        try:
            # 生成 SQL
            gen_result = self.generate_sql_query(conversation)
            
            if gen_result["status"] == "input_required":
                task.status = TaskStatus(
                    state=TaskState.INPUT_REQUIRED,
                    message={"role": "agent", "content": {"text": gen_result["message"]}}
                )
                return task
            
            sql_query = gen_result["sql"]
            query_type = gen_result["type"]
            logger.info(f"生成 SQL ({query_type}): {sql_query}")
            
            # 调用 MCP
            ticket_result = asyncio.run(get_tickets(sql_query))
            response = json.loads(ticket_result) if isinstance(ticket_result, str) else ticket_result
            logger.info(f"MCP 返回: {response}")
            
            # 格式化结果
            if response.get("status") == "success":
                data = response.get("data", [])
                lines = []
                for d in data:
                    if query_type == "train":
                        line = f"{d.get('train_no', '')} | {d.get('from_city', '')}→{d.get('to_city', '')} | {d.get('travel_date', '')} {d.get('departure_time', '')} | 二等座¥{d.get('price_second', '')} 余{d.get('stock_second', '')}张"
                        lines.append(line)
                    elif query_type == "flight":
                        line = f"{d.get('flight_no', '')} | {d.get('from_city', '')}→{d.get('to_city', '')} | {d.get('flight_date', '')} | 经济舱¥{d.get('price_economy', '')}"
                        lines.append(line)
                    elif query_type == "concert":
                        line = f"{d.get('concert_name', '')} | {d.get('artist', '')} | {d.get('city', '')} {d.get('venue', '')} | 日期:{d.get('show_date', '')} | 票价:¥{d.get('price_min', '')}-¥{d.get('price_max', '')} | 状态:{d.get('status', '')}"
                        lines.append(line)
                
                response_text = "\n".join(lines) if lines else "未查询到数据"
                task.artifacts = [{"parts": [{"type": "text", "text": response_text}]}]
                task.status = TaskStatus(state=TaskState.COMPLETED)
            else:
                task.status = TaskStatus(
                    state=TaskState.INPUT_REQUIRED,
                    message={"role": "agent", "content": {"text": response.get("message", "请重新输入")}}
                )
            
            return task
        except Exception as e:
            logger.error(f"处理失败: {e}")
            task.status = TaskStatus(
                state=TaskState.FAILED,
                message={"role": "agent", "content": {"text": f"查询失败: {e}"}}
            )
            return task


if __name__ == "__main__":
    server = TicketQueryServer()
    print("=" * 50)
    print("票务 A2A Agent 服务器")
    print("=" * 50)
    print(f"名称: {server.agent_card.name}")
    print(f"端口: 5006")
    print(f"依赖: MCP票务服务器 (8001)")
    print("=" * 50)
    run_server(server, host="127.0.0.1", port=5006)
