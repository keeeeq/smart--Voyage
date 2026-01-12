# -*- coding: utf-8 -*-
"""
提示词管理模块
==============
集中管理所有 LLM 提示词模板。
"""

from langchain_core.prompts import ChatPromptTemplate


class SmartVoyagePrompts:
    """SmartVoyage 提示词集合"""
    
    @staticmethod
    def intent_prompt():
        """意图识别提示词"""
        return ChatPromptTemplate.from_template("""
系统提示：您是一个专业的旅行意图识别专家。分析用户查询，识别意图并改写问题。

支持的意图：
- weather: 天气查询
- train: 火车票查询
- flight: 机票查询
- concert: 演唱会查询
- order: 票务预定
- out_of_scope: 超出范围

规则：
1. 识别意图，可以是多个，如 ["weather", "flight"]
2. 如果意图明确，改写用户问题使其更清晰
3. 如果意图不明确，生成追问消息
4. 输出严格 JSON 格式

输出格式：
{{
    "intents": ["intent1", "intent2"],
    "user_queries": {{"intent1": "改写后的问题1", "intent2": "改写后的问题2"}},
    "follow_up_message": "追问消息（如果需要）"
}}

示例：
- 输入: 北京明天天气
  输出: {{"intents": ["weather"], "user_queries": {{"weather": "北京 2026-01-13 天气"}}, "follow_up_message": ""}}
  
- 输入: 你好
  输出: {{"intents": ["out_of_scope"], "user_queries": {{}}, "follow_up_message": "你好，我是智能旅行助手，请问有什么可以帮您？"}}

当前日期：{current_date}
对话历史：{conversation_history}
用户查询：{query}
""")
    
    @staticmethod
    def summarize_weather_prompt():
        """天气结果总结提示词"""
        return ChatPromptTemplate.from_template("""
您是一位专业的天气预报员。基于查询结果生成总结：
- 突出城市、日期、温度、天气描述
- 使用预报员语气
- 保持中文，100-150字

查询：{query}
结果：{raw_response}
""")
    
    @staticmethod
    def summarize_ticket_prompt():
        """票务结果总结提示词"""
        return ChatPromptTemplate.from_template("""
您是一位专业的旅行顾问。基于查询结果生成总结。

严格规则：
1. 只使用结果中提供的信息，禁止编造任何数据
2. 日期、时间、价格必须与结果中的数据完全一致
3. 如果结果中没有某信息，不要猜测，直接省略
4. 不要添加推荐、建议或广告
5. 保持简洁，50-100字

查询：{query}
结果：{raw_response}
""")
    
    @staticmethod
    def attraction_prompt():
        """景点推荐提示词"""
        return ChatPromptTemplate.from_template("""
您是一位旅行专家。基于用户查询生成景点推荐：
- 推荐3-5个景点
- 包含描述、理由、注意事项
- 保持中文，150-250字

查询：{query}
""")


if __name__ == '__main__':
    print("提示词模块加载成功")
    print(SmartVoyagePrompts.intent_prompt())
