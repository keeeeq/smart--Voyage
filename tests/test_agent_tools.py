# -*- coding: utf-8 -*-
"""
Agent 工具调用测试
==================
测试 LangChain 工具绑定和调用流程。

使用方法:
    pytest tests/test_agent_tools.py -s
"""
import sys
from pathlib import Path

# 添加项目根目录到 sys.path，确保能正确导入 config
sys.path.insert(0, str(Path(__file__).parent.parent))

from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, ToolMessage
from langchain_core.tools import tool

from config import settings


# ========== 第一步：定义工具函数 ==========
@tool
def add(a: int, b: int) -> int:
    """
    将数字 a 与数字 b 相加

    Args:
        a: 第一个数字
        b: 第二个数字

    Returns:
        两数之和
    """
    return a + b


@tool
def multiply(a: int, b: int) -> int:
    """
    将数字 a 与数字 b 相乘

    Args:
        a: 第一个数字
        b: 第二个数字

    Returns:
        两数之积
    """
    return a * b


# 工具列表
tools = [add, multiply]


def test_agent_tool_calling():
    """
    测试 Agent 工具调用流程

    此测试验证：
    1. LLM 能正确识别需要调用的工具
    2. 工具能被正确执行
    3. 工具结果能被正确传回 LLM
    """
    # ========== 第二步：初始化模型 ==========
    llm = ChatOpenAI(
        base_url=settings.openai_base_url,
        api_key=settings.openai_api_key,
        model=settings.openai_model,
        temperature=0.1
    )

    # 绑定工具，允许模型自动选择工具
    llm_with_tools = llm.bind_tools(tools, tool_choice="auto")

    # ========== 第三步：调用回复 ==========
    query = "2+1等于多少？"
    messages = [HumanMessage(query)]

    # 第一次调用
    ai_msg = llm_with_tools.invoke(messages)
    messages.append(ai_msg)
    print(f"\n第一轮调用后结果：\n{messages}")

    # 处理工具调用
    if hasattr(ai_msg, 'tool_calls') and ai_msg.tool_calls:
        for tool_call in ai_msg.tool_calls:
            # 根据工具名称选择对应工具
            tool_name = tool_call["name"].lower()
            selected_tool = {"add": add, "multiply": multiply}.get(tool_name)

            if selected_tool:
                tool_output = selected_tool.invoke(tool_call["args"])
                messages.append(ToolMessage(
                    content=str(tool_output),
                    tool_call_id=tool_call["id"]
                ))

        print(f"\n第二轮 - 添加 tool_output 后：\n{messages}")

        # 第二次调用：将工具结果传回模型以生成最终回答
        final_response = llm_with_tools.invoke(messages)
        print(f"\n最终模型响应：\n{final_response.content}")

        # 验证最终响应包含正确答案
        assert "3" in final_response.content, "模型应该返回正确答案 3"
    else:
        print("模型未生成工具调用，直接返回文本:")
        print(ai_msg.content)


if __name__ == "__main__":
    # 允许直接运行此文件进行测试
    try:
        test_agent_tool_calling()
        print("\n✅ 测试通过！")
    except Exception as e:
        print(f"\n❌ 测试失败: {str(e)}")
