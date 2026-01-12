# -*- coding: utf-8 -*-
"""
SmartVoyage API 网关
====================
统一入口，负责意图识别、Agent 路由和结果润色。

使用方式:
    uvicorn api_gateway:app --host 0.0.0.0 --port 8000

端口: 8000
"""

import json
import re
import asyncio
import uuid
import logging
from datetime import datetime
from typing import Optional

import pytz
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from langchain_openai import ChatOpenAI
from python_a2a import AgentNetwork, TextContent, Message, MessageRole, Task

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
from config import settings
from main_prompts import SmartVoyagePrompts

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 创建 FastAPI 应用
app = FastAPI(
    title="SmartVoyage API Gateway",
    description="智能旅行助手 API 网关",
    version="1.0.0"
)

# CORS 配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 初始化 LLM
llm = ChatOpenAI(
    model=settings.openai_model,
    api_key=settings.openai_api_key,
    base_url=settings.openai_base_url,
    temperature=0.1
)

# 初始化 Agent 网络
agent_network = AgentNetwork(name="SmartVoyage Network")
agent_network.add("WeatherQueryAssistant", "http://localhost:5005")
agent_network.add("TicketQueryAssistant", "http://localhost:5006")
agent_network.add("TicketOrderAssistant", "http://localhost:5007")

# 会话历史存储（简单内存实现）
session_history: dict = {}


# 请求/响应模型
class ChatRequest(BaseModel):
    message: str
    session_id: Optional[str] = None


class ChatResponse(BaseModel):
    response: str
    intents: list
    agent_used: Optional[str] = None
    session_id: str


def intent_recognize(user_input: str, conversation_history: str) -> tuple:
    """意图识别"""
    try:
        chain = SmartVoyagePrompts.intent_prompt() | llm
        current_date = datetime.now(pytz.timezone('Asia/Shanghai')).strftime('%Y-%m-%d')
        
        response = chain.invoke({
            "conversation_history": conversation_history,
            "query": user_input,
            "current_date": current_date
        }).content.strip()
        
        response = re.sub(r'^```json\s*|\s*```$', '', response).strip()
        result = json.loads(response)
        
        return (
            result.get("intents", []),
            result.get("user_queries", {}),
            result.get("follow_up_message", "")
        )
    except Exception as e:
        logger.error(f"意图识别失败: {e}")
        return [], {}, "抱歉，我没有理解您的意思，请重试。"


async def call_agent(agent_name: str, query: str, history: str) -> str:
    """调用 Agent"""
    try:
        agent = agent_network.get_agent(agent_name)
        full_query = f"{history}\nUser: {query}" if history else query
        
        message = Message(content=TextContent(text=full_query), role=MessageRole.USER)
        task = Task(id="task-" + str(uuid.uuid4()), message=message.to_dict())
        result = await agent.send_task_async(task)
        
        if result.status.state == 'completed':
            return result.artifacts[0]['parts'][0]['text']
        else:
            return result.status.message.get('content', {}).get('text', '查询失败')
    except Exception as e:
        logger.error(f"调用 Agent 失败: {e}")
        return f"服务暂时不可用: {e}"


def summarize_result(intent: str, query: str, raw_response: str) -> str:
    """结果润色"""
    try:
        if intent == "weather":
            chain = SmartVoyagePrompts.summarize_weather_prompt() | llm
        else:
            chain = SmartVoyagePrompts.summarize_ticket_prompt() | llm
        
        return chain.invoke({
            "query": query,
            "raw_response": raw_response
        }).content.strip()
    except Exception as e:
        logger.error(f"结果润色失败: {e}")
        return raw_response


@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """
    聊天接口
    
    - 意图识别
    - Agent 路由
    - 结果润色
    """
    # 生成或获取 session_id
    session_id = request.session_id or str(uuid.uuid4())
    
    # 获取会话历史
    history = session_history.get(session_id, "")
    recent_history = '\n'.join(history.split("\n")[-6:]) if history else ""
    
    logger.info(f"[{session_id}] 收到消息: {request.message}")
    
    # 意图识别
    intents, user_queries, follow_up = intent_recognize(request.message, recent_history)
    logger.info(f"[{session_id}] 识别意图: {intents}")
    
    # 处理超出范围或需要追问
    if "out_of_scope" in intents or follow_up:
        response = follow_up or "请提供旅行相关的查询。"
        session_history[session_id] = history + f"\nUser: {request.message}\nAssistant: {response}"
        return ChatResponse(
            response=response,
            intents=intents,
            session_id=session_id
        )
    
    # 调用 Agent
    responses = []
    agent_used = None
    
    for intent in intents:
        if intent == "weather":
            agent_name = "WeatherQueryAssistant"
        elif intent in ["train", "flight", "concert"]:
            agent_name = "TicketQueryAssistant"
        elif intent == "order":
            agent_name = "TicketOrderAssistant"
        else:
            continue
        
        agent_used = agent_name
        query = user_queries.get(intent, request.message)
        
        # 调用 Agent
        raw_result = await call_agent(agent_name, query, recent_history)
        logger.info(f"[{session_id}] Agent 返回: {raw_result[:100]}...")
        
        # 结果润色（订票不需要润色）
        if agent_name != "TicketOrderAssistant":
            result = summarize_result(intent, query, raw_result)
        else:
            result = raw_result
        
        responses.append(result)
    
    final_response = "\n\n".join(responses) if responses else "暂不支持此查询。"
    
    # 更新会话历史
    session_history[session_id] = history + f"\nUser: {request.message}\nAssistant: {final_response}"
    
    return ChatResponse(
        response=final_response,
        intents=intents,
        agent_used=agent_used,
        session_id=session_id
    )


@app.get("/health")
async def health_check():
    """健康检查"""
    return {"status": "ok", "service": "API Gateway"}


@app.get("/agents")
async def list_agents():
    """列出可用 Agent"""
    agents = []
    for name in ["WeatherQueryAssistant", "TicketQueryAssistant", "TicketOrderAssistant"]:
        try:
            card = agent_network.get_agent_card(name)
            agents.append({
                "name": name,
                "status": "online",
                "description": card.description
            })
        except:
            agents.append({
                "name": name,
                "status": "offline"
            })
    return {"agents": agents}


if __name__ == "__main__":
    import uvicorn
    print("=" * 50)
    print("SmartVoyage API 网关")
    print("=" * 50)
    print("端口: 8000")
    print("文档: http://localhost:8000/docs")
    print("=" * 50)
    uvicorn.run(app, host="0.0.0.0", port=8000)
