# -*- coding: utf-8 -*-
"""
意图识别模块
============
识别用户输入的意图并提取关键槽位信息。

知识点：
--------
1. 意图识别（Intent Recognition）：判断用户想做什么
2. 槽位填充（Slot Filling）：提取关键信息（城市、日期等）
3. 追问机制：当信息不完整时，询问用户补充
4. JSON 格式输出：让 LLM 返回结构化数据，便于程序处理
"""

import json
import logging
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, asdict
from enum import Enum

from langchain.prompts import PromptTemplate

from .chat_model import get_chat_model

# 配置日志
logger = logging.getLogger(__name__)


class Intent(Enum):
    """
    意图枚举
    
    知识点：
    --------
    使用枚举类型定义意图，比字符串更安全：
    - 防止拼写错误
    - IDE 自动补全
    - 类型检查
    """
    WEATHER = "weather"           # 天气查询
    TRAIN_TICKET = "train_ticket"  # 火车票查询
    FLIGHT_TICKET = "flight_ticket"  # 机票查询
    CONCERT = "concert"            # 演唱会查询
    UNKNOWN = "unknown"            # 未知意图
    CLARIFICATION = "clarification"  # 需要追问


@dataclass
class IntentResult:
    """
    意图识别结果
    
    知识点：
    --------
    @dataclass 是 Python 3.7+ 的特性，自动生成 __init__、__repr__ 等方法，
    非常适合用于存储结构化数据。
    """
    intent: str                     # 识别的意图
    confidence: float               # 置信度 (0-1)
    slots: Dict[str, Any]           # 提取的槽位
    missing_slots: List[str]        # 缺失的必要槽位
    clarification_question: Optional[str] = None  # 追问问题
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return asdict(self)
    
    @property
    def is_complete(self) -> bool:
        """槽位是否完整"""
        return len(self.missing_slots) == 0


# 意图识别提示词模板
INTENT_RECOGNITION_PROMPT = """你是一个意图识别助手。分析用户输入，识别意图并提取关键信息。

### 支持的意图类型

1. **weather** (天气查询)
   - 必要槽位: city (城市)
   - 可选槽位: date (日期)
   - 示例: "北京明天天气", "天气", "上海这周末天气怎么样"

2. **train_ticket** (火车票查询)
   - 必要槽位: from_city (出发城市), to_city (到达城市)
   - 可选槽位: date (日期)
   - 示例: "北京到上海的火车票", "明天从广州去深圳"

3. **flight_ticket** (机票查询)
   - 必要槽位: from_city (出发城市), to_city (到达城市)
   - 可选槽位: date (日期)
   - 示例: "北京飞上海", "下周三从成都到杭州的机票"

4. **concert** (演唱会查询)
   - 可选槽位: city (城市), artist (艺人), date (日期)
   - 示例: "周杰伦演唱会", "北京最近有什么演唱会"

5. **unknown** (未知意图)
   - 无法识别的请求

### 槽位提取规则

- **city/from_city/to_city**: 提取中国城市名称
- **date**: 转换为具体日期或日期描述
  - "今天"、"明天"、"后天" -> 保持原样
  - "下周一" -> "next_monday"
  - "这周末" -> "this_weekend"
  - "近X天" -> "next_X_days"
  - 如果没有提到日期，设为 null

### 追问规则

当必要槽位缺失时，生成友好的追问问题：
- 天气缺少城市: "请问您想查询哪个城市的天气？"
- 火车票缺少目的地: "请问您想去哪个城市？"
- 火车票缺少出发地: "请问您从哪个城市出发？"

### 特殊规则

- 如果用户只说 "天气"，意图是 weather，城市设为 null，不需要追问（系统会返回默认城市）
- 如果用户说 "火车票" 但没有任何城市信息，需要追问

### 输出格式（严格 JSON）

```json
{{
  "intent": "意图类型",
  "confidence": 0.95,
  "slots": {{
    "city": "城市名或null",
    "from_city": "出发城市或null",
    "to_city": "到达城市或null",
    "date": "日期描述或null",
    "artist": "艺人名或null"
  }},
  "missing_slots": ["缺失的必要槽位列表"],
  "clarification_question": "追问问题或null"
}}
```

### 用户输入
{user_input}

### 分析结果（只输出 JSON，不要其他内容）
"""


class IntentRecognizer:
    """
    意图识别器
    
    识别用户输入的意图，提取槽位信息，必要时生成追问。
    """
    
    def __init__(self):
        """初始化意图识别器"""
        self.llm = get_chat_model(temperature=0.0)
        self.prompt = PromptTemplate(
            input_variables=["user_input"],
            template=INTENT_RECOGNITION_PROMPT
        )
    
    def recognize(self, user_input: str) -> IntentResult:
        """
        识别用户意图
        
        Args:
            user_input: 用户输入文本
        
        Returns:
            IntentResult 意图识别结果
        
        知识点：
        --------
        让 LLM 输出 JSON 的技巧：
        1. 在 prompt 中明确要求输出 JSON 格式
        2. 提供 JSON 模板示例
        3. 强调"只输出 JSON，不要其他内容"
        4. 使用低温度参数确保输出稳定
        """
        logger.info(f"识别意图: {user_input}")
        
        full_prompt = self.prompt.format(user_input=user_input)
        
        try:
            response = self.llm.invoke(full_prompt)
            result = self._parse_response(response.content)
            
            logger.info(f"意图: {result.intent}, 置信度: {result.confidence}")
            logger.debug(f"槽位: {result.slots}")
            
            return result
            
        except Exception as e:
            logger.error(f"意图识别失败: {e}")
            return IntentResult(
                intent=Intent.UNKNOWN.value,
                confidence=0.0,
                slots={},
                missing_slots=[],
                clarification_question="抱歉，我没有理解您的意思，请换个方式描述。"
            )
    
    def _parse_response(self, text: str) -> IntentResult:
        """
        解析 LLM 响应
        
        Args:
            text: LLM 返回的文本
        
        Returns:
            IntentResult
        """
        # 尝试提取 JSON
        import re
        
        # 查找 JSON 块
        json_pattern = r"\{[\s\S]*\}"
        match = re.search(json_pattern, text)
        
        if match:
            try:
                data = json.loads(match.group())
                
                return IntentResult(
                    intent=data.get("intent", Intent.UNKNOWN.value),
                    confidence=float(data.get("confidence", 0.8)),
                    slots=data.get("slots", {}),
                    missing_slots=data.get("missing_slots", []),
                    clarification_question=data.get("clarification_question")
                )
            except json.JSONDecodeError as e:
                logger.error(f"JSON 解析失败: {e}, 原文: {text}")
        
        # 解析失败，返回未知意图
        return IntentResult(
            intent=Intent.UNKNOWN.value,
            confidence=0.0,
            slots={},
            missing_slots=[],
            clarification_question="抱歉，我没有理解您的意思。"
        )
    
    def needs_clarification(self, result: IntentResult) -> bool:
        """
        判断是否需要追问
        
        Args:
            result: 意图识别结果
        
        Returns:
            是否需要追问
        
        逻辑：
        - 天气：城市可以为空（返回默认城市），不追问
        - 火车票/机票：必须有 from_city 和 to_city
        - 演唱会：都是可选槽位，不追问
        - 未知：不追问，直接返回无法理解
        """
        intent = result.intent
        slots = result.slots or {}
        
        # 天气查询：不追问
        if intent == "weather":
            return False
        
        # 火车票/机票：检查必要槽位
        if intent in ["train_ticket", "flight_ticket"]:
            from_city = slots.get("from_city")
            to_city = slots.get("to_city")
            # 如果 from_city 和 to_city 都有值（非空、非 null），则不需要追问
            if from_city and to_city and from_city.lower() != "null" and to_city.lower() != "null":
                return False
            return True
        
        # 演唱会：不追问
        if intent == "concert":
            return False
        
        # 其他情况：不追问
        return False


if __name__ == "__main__":
    # 测试意图识别
    import colorlog
    
    # 配置彩色日志
    handler = colorlog.StreamHandler()
    handler.setFormatter(colorlog.ColoredFormatter(
        '%(log_color)s%(levelname)s: %(message)s'
    ))
    logging.getLogger().addHandler(handler)
    logging.getLogger().setLevel(logging.INFO)
    
    print("=" * 50)
    print("测试意图识别器")
    print("=" * 50)
    
    recognizer = IntentRecognizer()
    
    # 测试用例
    test_inputs = [
        "北京明天天气怎么样",
        "天气",
        "上海到北京的火车票",
        "火车票",
        "周杰伦北京演唱会",
        "你好",
    ]
    
    for user_input in test_inputs:
        print(f"\n输入: {user_input}")
        result = recognizer.recognize(user_input)
        print(f"意图: {result.intent} (置信度: {result.confidence})")
        print(f"槽位: {result.slots}")
        if result.clarification_question:
            print(f"追问: {result.clarification_question}")
    
    print("\n" + "=" * 50)
