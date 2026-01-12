# -*- coding: utf-8 -*-
"""
订票 A2A Agent 服务器
====================
先调用票务 Agent 查询余票，然后调用订票 MCP 完成预定。

使用方式:
    python a2a_server/order_server.py

端口: 5007
依赖: 
    - 票务 A2A Agent (5006)
    - 订票 MCP 服务器 (8003)
"""

import json
import asyncio
import uuid
import logging

from langchain_openai import ChatOpenAI
from mcp import ClientSession
from mcp.client.streamable_http import streamablehttp_client
from langchain_mcp_adapters.tools import load_mcp_tools
from langchain.agents import create_tool_calling_agent, AgentExecutor
from langchain_core.prompts import ChatPromptTemplate
from python_a2a import (
    A2AServer, run_server, AgentCard, AgentSkill, TaskStatus, TaskState,
    A2AClient, Message, TextContent, MessageRole, Task
)

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


async def order_tickets(query: str) -> dict:
    """调用订票 MCP 服务器"""
    try:
        async with streamablehttp_client("http://127.0.0.1:8003/mcp") as (read, write, _):
            async with ClientSession(read, write) as session:
                await session.initialize()
                tools = await load_mcp_tools(session)
                
                prompt = ChatPromptTemplate.from_messages([
                    ("system", """你是票务预定助手，根据用户信息调用工具完成预定。

回复规则：
1. 只输出预定结果，不要添加任何推荐、建议或广告
2. 不要提及任何第三方平台（如大麦、猫眼等）
3. 回复简洁，只包含：预定成功/失败、票务信息、数量
4. 不要添加祝福语、表情符号或营销话术

示例回复：预定成功！1张五月天上海演唱会门票（280元档）"""),
                    ("human", "{input}"),
                    ("placeholder", "{agent_scratchpad}"),
                ])
                
                agent = create_tool_calling_agent(llm, tools, prompt)
                executor = AgentExecutor(agent=agent, tools=tools, verbose=True)
                response = await executor.ainvoke({"input": query})
                
                return {"status": "success", "message": response['output']}
    except Exception as e:
        logger.error(f"调用订票 MCP 失败: {e}")
        return {"status": "error", "message": str(e)}


# Agent Card 定义
agent_card = AgentCard(
    name="TicketOrderAssistant",
    description="票务预定助手，先查询余票再完成预定",
    url="http://localhost:5007",
    version="1.0.0",
    capabilities={"streaming": True, "memory": True},
    skills=[
        AgentSkill(
            name="execute ticket order",
            description="执行票务预定（火车票、机票、演唱会票）",
            examples=["订一张明天北京到上海的火车票", "预定2张飞机票"]
        )
    ]
)


class TicketOrderServer(A2AServer):
    """订票 A2A 服务器"""
    
    def __init__(self):
        super().__init__(agent_card=agent_card)
        self.ticket_client = A2AClient("http://localhost:5006")
    
    def handle_task(self, task):
        """处理任务"""
        content = (task.message or {}).get("content", {})
        conversation = content.get("text", "") if isinstance(content, dict) else ""
        logger.info(f"收到订票请求: {conversation}")
        
        try:
            # 1. 先调用票务 Agent 查询余票
            message = Message(content=TextContent(text=conversation), role=MessageRole.USER)
            ticket_task = Task(id="task-" + str(uuid.uuid4()), message=message.to_dict())
            ticket_result = asyncio.run(self.ticket_client.send_task_async(ticket_task))
            
            logger.info(f"票务查询结果: {ticket_result}")
            
            if ticket_result.status.state != 'completed':
                # 余票查询失败
                msg = ticket_result.status.message.get('content', {}).get('text', '查询失败')
                task.status = TaskStatus(
                    state=TaskState.INPUT_REQUIRED,
                    message={"role": "agent", "content": {"text": msg}}
                )
                return task
            
            ticket_info = ticket_result.artifacts[0]["parts"][0]["text"]
            logger.info(f"余票信息: {ticket_info}")
            
            # 2. 调用订票 MCP 完成预定
            order_query = f"{conversation}\n余票信息：{ticket_info}"
            order_result = asyncio.run(order_tickets(order_query))
            logger.info(f"订票结果: {order_result}")
            
            if order_result.get("status") == "success":
                response_text = f"余票信息：\n{ticket_info}\n\n订票结果：{order_result['message']}"
                task.artifacts = [{"parts": [{"type": "text", "text": response_text}]}]
                task.status = TaskStatus(state=TaskState.COMPLETED)
            else:
                task.status = TaskStatus(
                    state=TaskState.FAILED,
                    message={"role": "agent", "content": {"text": order_result.get("message", "预定失败")}}
                )
            
            return task
        except Exception as e:
            logger.error(f"处理失败: {e}")
            task.status = TaskStatus(
                state=TaskState.FAILED,
                message={"role": "agent", "content": {"text": f"预定失败: {e}"}}
            )
            return task


if __name__ == "__main__":
    server = TicketOrderServer()
    print("=" * 50)
    print("订票 A2A Agent 服务器")
    print("=" * 50)
    print(f"名称: {server.agent_card.name}")
    print(f"端口: 5007")
    print(f"依赖: 票务Agent(5006), 订票MCP(8003)")
    print("=" * 50)
    run_server(server, host="127.0.0.1", port=5007)
