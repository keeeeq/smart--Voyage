# -*- coding: utf-8 -*-
"""
天气 A2A Agent 服务器
====================
使用 LLM 生成 SQL 查询天气 MCP 工具，返回用户友好文本结果。

使用方式:
    python a2a_server/weather_server.py

端口: 5005
依赖: MCP天气服务器 (8002)
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

# 天气表 Schema（用于 SQL 生成 Prompt）
TABLE_SCHEMA = """
CREATE TABLE weather_data (
    city VARCHAR(50) NOT NULL COMMENT '城市名称',
    fx_date DATE NOT NULL COMMENT '预报日期',
    temp_max INT COMMENT '最高温度',
    temp_min INT COMMENT '最低温度',
    text_day VARCHAR(20) COMMENT '白天天气描述',
    text_night VARCHAR(20) COMMENT '夜间天气描述',
    humidity INT COMMENT '相对湿度 (%)',
    wind_dir_day VARCHAR(20) COMMENT '白天风向',
    precip DECIMAL(5,1) COMMENT '降水量 (mm)',
    UNIQUE KEY (city, fx_date)
);
"""

# SQL 生成提示词
SQL_PROMPT = ChatPromptTemplate.from_template("""
系统提示：你是一个专业的天气SQL生成器，基于 weather_data 表生成 SELECT 语句。

规则：
- 如果用户需要查天气，至少需要城市和时间信息
- 如果信息不足，返回 JSON：{{"status": "input_required", "message": "追问内容"}}
- 如果信息充足，返回纯 SQL 语句

示例：
- 输入: 北京 2026-01-12
  输出: SELECT city, fx_date, temp_max, temp_min, text_day, text_night, humidity, wind_dir_day, precip FROM weather_data WHERE city = '北京' AND fx_date = '2026-01-12'
- 输入: 北京的天气
  输出: {{"status": "input_required", "message": "请提供具体日期，例如 '2026-01-12'"}}

表结构：{schema}
对话历史: {conversation}
当前日期: {current_date}
""")


async def get_weather(sql: str) -> dict:
    """调用天气 MCP 服务器"""
    try:
        async with streamablehttp_client("http://127.0.0.1:8002/mcp") as (read, write, _):
            async with ClientSession(read, write) as session:
                await session.initialize()
                result = await session.call_tool("query_weather", {"sql": sql})
                return result.content[0].text
    except Exception as e:
        logger.error(f"调用天气 MCP 失败: {e}")
        return json.dumps({"status": "error", "message": str(e)})


# Agent Card 定义
agent_card = AgentCard(
    name="WeatherQueryAssistant",
    description="基于 LangChain 提供天气查询服务的助手",
    url="http://localhost:5005",
    version="1.0.0",
    capabilities={"streaming": True, "memory": True},
    skills=[
        AgentSkill(
            name="execute weather query",
            description="执行天气查询，返回天气数据库结果",
            examples=["北京 2026-01-12 天气", "上海未来3天", "今天天气如何"]
        )
    ]
)


class WeatherQueryServer(A2AServer):
    """天气查询 A2A 服务器"""
    
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
                "current_date": current_date,
                "schema": TABLE_SCHEMA
            }).content.strip()
            
            logger.info(f"LLM 输出: {output}")
            
            if output.startswith('{'):
                return json.loads(output)
            return {"status": "sql", "sql": output}
        except Exception as e:
            logger.error(f"SQL 生成失败: {e}")
            return {"status": "input_required", "message": "查询无效，请提供城市和日期。"}
    
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
            logger.info(f"生成 SQL: {sql_query}")
            
            # 调用 MCP
            weather_result = asyncio.run(get_weather(sql_query))
            response = json.loads(weather_result) if isinstance(weather_result, str) else weather_result
            logger.info(f"MCP 返回: {response}")
            
            # 格式化结果
            if response.get("status") == "success":
                data = response.get("data", [])
                lines = []
                for d in data:
                    lines.append(
                        f"{d['city']} {d['fx_date']}: {d['text_day']}（夜间 {d['text_night']}），"
                        f"温度 {d['temp_min']}-{d['temp_max']}°C，湿度 {d['humidity']}%，"
                        f"风向 {d['wind_dir_day']}，降水 {d.get('precip', 0)}mm"
                    )
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
    server = WeatherQueryServer()
    print("=" * 50)
    print("天气 A2A Agent 服务器")
    print("=" * 50)
    print(f"名称: {server.agent_card.name}")
    print(f"端口: 5005")
    print(f"依赖: MCP天气服务器 (8002)")
    print("=" * 50)
    run_server(server, host="127.0.0.1", port=5005)
