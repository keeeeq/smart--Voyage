# -*- coding: utf-8 -*-
"""
SmartVoyage 客户端主程序
========================
基于 A2A 协议的智能旅行助手客户端。

功能：
1. 意图识别
2. 路由到对应 Agent
3. 整合结果返回

使用方式（命令行测试）：
    python smart_voyage_main.py
"""

import asyncio
import json
import uuid
import re
import logging
from datetime import datetime

import pytz
from python_a2a import AgentNetwork, TextContent, Message, MessageRole, Task
from langchain_openai import ChatOpenAI

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
from config import settings
from main_prompts import SmartVoyagePrompts

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class SmartVoyageClient:
    """SmartVoyage 客户端"""
    
    def __init__(self):
        """初始化客户端"""
        # Agent 网络
        self.agent_network = AgentNetwork(name="SmartVoyage Network")
        self.agent_network.add("WeatherQueryAssistant", "http://localhost:5005")
        self.agent_network.add("TicketQueryAssistant", "http://localhost:5006")
        self.agent_network.add("TicketOrderAssistant", "http://localhost:5007")
        
        # Agent URL 信息
        self.agent_urls = {
            "WeatherQueryAssistant": "http://localhost:5005",
            "TicketQueryAssistant": "http://localhost:5006",
            "TicketOrderAssistant": "http://localhost:5007"
        }
        
        # LLM
        self.llm = ChatOpenAI(
            model=settings.openai_model,
            api_key=settings.openai_api_key,
            base_url=settings.openai_base_url,
            temperature=0.1
        )
        
        # 对话历史
        self.conversation_history = ""
        self.messages = []
        
        logger.info("SmartVoyage 客户端初始化完成")
    
    def intent_recognize(self, user_input: str) -> tuple:
        """
        意图识别
        
        Returns:
            (intents, user_queries, follow_up_message)
        """
        chain = SmartVoyagePrompts.intent_prompt() | self.llm
        current_date = datetime.now(pytz.timezone('Asia/Shanghai')).strftime('%Y-%m-%d')
        
        # 只取最近6轮对话
        recent_history = '\n'.join(self.conversation_history.split("\n")[-6:])
        
        response = chain.invoke({
            "conversation_history": recent_history,
            "query": user_input,
            "current_date": current_date
        }).content.strip()
        
        logger.info(f"意图识别原始响应: {response}")
        
        # 清理 Markdown 代码块标记
        response = re.sub(r'^```json\s*|\s*```$', '', response).strip()
        
        result = json.loads(response)
        intents = result.get("intents", [])
        user_queries = result.get("user_queries", {})
        follow_up_message = result.get("follow_up_message", "")
        
        logger.info(f"意图: {intents}, 改写查询: {user_queries}")
        
        return intents, user_queries, follow_up_message
    
    async def call_agent(self, agent_name: str, query: str) -> str:
        """调用指定 Agent"""
        try:
            agent = self.agent_network.get_agent(agent_name)
            
            # 构建消息
            chat_history = '\n'.join(self.conversation_history.split("\n")[-6:])
            full_query = f"{chat_history}\nUser: {query}"
            
            message = Message(content=TextContent(text=full_query), role=MessageRole.USER)
            task = Task(id="task-" + str(uuid.uuid4()), message=message.to_dict())
            
            result = await agent.send_task_async(task)
            logger.info(f"{agent_name} 响应: {result}")
            
            if result.status.state == 'completed':
                return result.artifacts[0]['parts'][0]['text']
            else:
                return result.status.message.get('content', {}).get('text', '查询失败')
        except Exception as e:
            logger.error(f"调用 {agent_name} 失败: {e}")
            return f"查询失败: {e}"
    
    def process_input(self, user_input: str) -> str:
        """
        处理用户输入
        
        Args:
            user_input: 用户输入文本
        
        Returns:
            助手响应
        """
        # 更新对话历史
        self.messages.append({"role": "user", "content": user_input})
        self.conversation_history += f"\nUser: {user_input}"
        
        try:
            # 意图识别
            intents, user_queries, follow_up_message = self.intent_recognize(user_input)
            
            # 处理超出范围或需要追问
            if "out_of_scope" in intents or follow_up_message:
                response = follow_up_message or "请提供旅行相关的查询。"
                self.conversation_history += f"\nAssistant: {response}"
                self.messages.append({"role": "assistant", "content": response})
                return response
            
            # 处理有效意图
            responses = []
            for intent in intents:
                # 确定 Agent
                if intent == "weather":
                    agent_name = "WeatherQueryAssistant"
                elif intent in ["train", "flight", "concert"]:
                    agent_name = "TicketQueryAssistant"
                elif intent == "order":
                    agent_name = "TicketOrderAssistant"
                else:
                    continue
                
                # 获取改写后的查询
                query = user_queries.get(intent, user_input)
                
                # 调用 Agent
                result = asyncio.run(self.call_agent(agent_name, query))
                
                # 使用 LLM 总结结果
                if agent_name == "WeatherQueryAssistant":
                    chain = SmartVoyagePrompts.summarize_weather_prompt() | self.llm
                    summary = chain.invoke({"query": query, "raw_response": result}).content.strip()
                    responses.append(summary)
                elif agent_name == "TicketQueryAssistant":
                    chain = SmartVoyagePrompts.summarize_ticket_prompt() | self.llm
                    summary = chain.invoke({"query": query, "raw_response": result}).content.strip()
                    responses.append(summary)
                else:
                    responses.append(result)
            
            response = "\n\n".join(responses) if responses else "暂不支持此查询。"
            
        except json.JSONDecodeError as e:
            logger.error(f"意图识别 JSON 解析失败: {e}")
            response = "抱歉，我没有理解您的意思，请重试。"
        except Exception as e:
            logger.error(f"处理失败: {e}")
            response = f"处理失败: {e}"
        
        # 更新历史
        self.conversation_history += f"\nAssistant: {response}"
        self.messages.append({"role": "assistant", "content": response})
        
        return response
    
    def get_agent_cards(self) -> dict:
        """获取所有 Agent 卡片信息"""
        cards = {}
        for name in self.agent_network.agents.keys():
            try:
                card = self.agent_network.get_agent_card(name)
                cards[name] = {
                    "description": card.description,
                    "skills": [s.name for s in card.skills] if card.skills else [],
                    "url": self.agent_urls.get(name, "")
                }
            except:
                cards[name] = {"description": "无法获取", "skills": [], "url": self.agent_urls.get(name, "")}
        return cards


# 命令行测试
if __name__ == "__main__":
    print("=" * 50)
    print("🤖 SmartVoyage 智能旅行助手")
    print("=" * 50)
    print("输入 'quit' 退出, 'cards' 查看 Agent 信息")
    print("=" * 50)
    
    client = SmartVoyageClient()
    
    # 显示 Agent 卡片
    print("\n📋 Agent 信息:")
    for name, info in client.get_agent_cards().items():
        print(f"  - {name}: {info['description']}")
    print()
    
    while True:
        try:
            user_input = input("您: ").strip()
            if user_input.lower() == 'quit':
                print("再见！")
                break
            elif user_input.lower() == 'cards':
                for name, info in client.get_agent_cards().items():
                    print(f"\n{name}:")
                    print(f"  描述: {info['description']}")
                    print(f"  技能: {info['skills']}")
                    print(f"  地址: {info['url']}")
                continue
            elif not user_input:
                continue
            
            response = client.process_input(user_input)
            print(f"\n助手: {response}\n")
        except KeyboardInterrupt:
            print("\n再见！")
            break
