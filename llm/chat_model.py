# -*- coding: utf-8 -*-
"""
LLM 模型封装模块
================
封装 LangChain ChatOpenAI，支持 OpenAI 兼容 API。

知识点：
--------
1. LangChain 是一个 LLM 应用开发框架，简化了与各种 LLM 的交互
2. ChatOpenAI 是 LangChain 中用于与 OpenAI API 交互的类
3. 通过设置 base_url，可以连接到 OpenAI 兼容的第三方 API（如通义千问）
4. temperature 参数控制回复的随机性（0=确定性，1=高随机性）
"""

import logging
from typing import Optional

from langchain_openai import ChatOpenAI

# 导入配置
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))
from config import settings

# 配置日志
logger = logging.getLogger(__name__)


def get_chat_model(
    temperature: float = 0.0,
    model: Optional[str] = None,
    streaming: bool = False
) -> ChatOpenAI:
    """
    获取 LLM 聊天模型实例
    
    Args:
        temperature: 温度参数，控制输出随机性（0-1）
                    - 0: 输出确定性高，适合 SQL 生成等需要精确结果的任务
                    - 0.7: 中等随机性，适合一般对话
                    - 1: 高随机性，适合创意写作
        model: 模型名称，默认使用配置文件中的模型
        streaming: 是否启用流式输出
    
    Returns:
        ChatOpenAI 实例
    
    知识点：
    --------
    LangChain ChatOpenAI 的重要参数：
    - api_key: API 密钥
    - base_url: API 基础 URL（支持兼容接口）
    - model: 模型名称（如 gpt-4, qwen-plus 等）
    - temperature: 温度参数
    - max_tokens: 最大输出 token 数
    - streaming: 流式输出（用于实时显示回复）
    """
    if not settings.openai_api_key:
        logger.error("OpenAI API Key 未配置，请检查 .env 文件")
        raise ValueError("OPENAI_API_KEY 未配置")
    
    model_name = model or settings.openai_model
    
    logger.info(f"初始化 LLM 模型: {model_name}")
    logger.debug(f"  - Base URL: {settings.openai_base_url}")
    logger.debug(f"  - Temperature: {temperature}")
    
    return ChatOpenAI(
        api_key=settings.openai_api_key,
        base_url=settings.openai_base_url,
        model=model_name,
        temperature=temperature,
        streaming=streaming,
    )


if __name__ == "__main__":
    # 测试 LLM 模型
    import colorlog
    
    # 配置彩色日志
    handler = colorlog.StreamHandler()
    handler.setFormatter(colorlog.ColoredFormatter(
        '%(log_color)s%(levelname)s: %(message)s'
    ))
    logging.getLogger().addHandler(handler)
    logging.getLogger().setLevel(logging.DEBUG)
    
    print("=" * 50)
    print("测试 LLM 模型")
    print("=" * 50)
    
    try:
        llm = get_chat_model(temperature=0.7)
        
        # 简单测试
        response = llm.invoke("你好，请用一句话介绍自己。")
        print(f"\n模型回复: {response.content}")
        
        print("\n" + "=" * 50)
        print("LLM 模型测试成功！")
        print("=" * 50)
    except Exception as e:
        print(f"测试失败: {e}")
