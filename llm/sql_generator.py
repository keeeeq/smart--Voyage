# -*- coding: utf-8 -*-
"""
SQL 生成模块
============
使用 LLM 将自然语言转换为 SQL 查询语句。

知识点：
--------
1. Prompt Engineering: 通过精心设计的提示词引导 LLM 生成符合要求的输出
2. Few-shot Learning: 在提示中提供示例，帮助 LLM 理解任务格式
3. Output Parsing: 解析 LLM 返回的文本，提取需要的信息
4. LangChain PromptTemplate: 模板化管理提示词，支持变量替换
"""

import re
import logging
from typing import Optional, Dict, Any
from datetime import datetime, timedelta

from langchain.prompts import PromptTemplate

from .chat_model import get_chat_model

# 配置日志
logger = logging.getLogger(__name__)


# SQL 生成提示词模板
SQL_GENERATION_PROMPT = """你是一个专业的 SQL 生成助手。根据用户的自然语言问题，生成正确的 MySQL 查询语句。

### 数据库表结构

1. **weather_data** (天气数据表)
   - city: 城市名称 (如：北京、上海)
   - fx_date: 预报日期 (DATE 类型，格式 YYYY-MM-DD)
   - temp_max: 最高温度 (整数)
   - temp_min: 最低温度 (整数)
   - text_day: 白天天气 (如：晴、多云、小雨)
   - text_night: 夜间天气
   - humidity: 相对湿度 (百分比)
   - uv_index: 紫外线指数

2. **train_ticket** (火车票表)
   - train_no: 车次号 (如：G1234)
   - from_city: 出发城市
   - to_city: 到达城市
   - from_station: 出发站
   - to_station: 到达站
   - departure_time: 出发时间 (TIME)
   - arrival_time: 到达时间 (TIME)
   - travel_date: 乘车日期 (DATE)
   - duration: 行程时长
   - price_second: 二等座票价
   - price_first: 一等座票价
   - stock_second: 二等座余票
   - stock_first: 一等座余票

3. **flight_ticket** (机票表)
   - flight_no: 航班号
   - airline: 航空公司
   - from_city: 出发城市
   - to_city: 到达城市
   - flight_date: 航班日期 (DATE)
   - price_economy: 经济舱票价

4. **concert_ticket** (演唱会票务表)
   - concert_name: 演唱会名称
   - artist: 艺人
   - city: 城市
   - venue: 场馆
   - show_date: 演出日期 (DATE)
   - status: 状态 (预售/在售/售罄/已结束)
   - price_min/price_max: 票价范围

### 当前时间信息
- 今天日期: {current_date}

### 日期处理规则
- "今天" -> {current_date}
- "明天" -> {tomorrow}
- "后天" -> {day_after_tomorrow}
- "下周X" -> 计算对应日期
- "未来N天" 或 "近N天" -> 从今天起的 N 天范围
- 如果用户没有指定日期，默认查询今天的数据

### 示例

问题: 北京明天天气怎么样？
```sql
SELECT city, fx_date, temp_max, temp_min, text_day, humidity 
FROM weather_data 
WHERE city = '北京' AND fx_date = '{tomorrow}'
```

问题: 上海到北京的火车票
```sql
SELECT train_no, from_station, to_station, departure_time, arrival_time, 
       duration, price_second, stock_second 
FROM train_ticket 
WHERE from_city = '上海' AND to_city = '北京' AND travel_date >= '{current_date}'
ORDER BY departure_time
LIMIT 10
```

问题: 天气
```sql
SELECT city, fx_date, temp_max, temp_min, text_day 
FROM weather_data 
WHERE city IN ('北京', '上海', '广州', '深圳') AND fx_date = '{current_date}'
```

### 要求
1. 只输出 SQL 语句，不要有任何解释
2. 使用 SELECT 语句，不要使用 INSERT/UPDATE/DELETE
3. 适当使用 LIMIT 限制返回数量（默认 10 条）
4. 日期比较使用 = 或 >= 或 BETWEEN
5. 只查询用户需要的字段，不要 SELECT *

### 用户问题
{question}

### SQL 查询
"""


class SQLGenerator:
    """
    SQL 生成器
    
    使用 LLM 将用户的自然语言问题转换为 SQL 查询语句。
    
    知识点：
    --------
    为什么使用 LLM 生成 SQL？
    - 自然语言理解：用户可以用日常语言提问
    - 灵活性：无需预定义所有查询模板
    - 智能日期处理：自动理解"明天"、"下周"等相对日期
    """
    
    def __init__(self):
        """初始化 SQL 生成器"""
        # 使用低温度参数，确保输出稳定
        self.llm = get_chat_model(temperature=0.0)
        
        # 创建提示模板
        self.prompt = PromptTemplate(
            input_variables=["question", "current_date", "tomorrow", "day_after_tomorrow"],
            template=SQL_GENERATION_PROMPT
        )
    
    def _get_date_context(self) -> Dict[str, str]:
        """
        获取日期上下文
        
        Returns:
            包含今天、明天、后天日期的字典
        """
        today = datetime.now().date()
        return {
            "current_date": today.strftime("%Y-%m-%d"),
            "tomorrow": (today + timedelta(days=1)).strftime("%Y-%m-%d"),
            "day_after_tomorrow": (today + timedelta(days=2)).strftime("%Y-%m-%d"),
        }
    
    def generate_sql(self, question: str) -> Optional[str]:
        """
        根据用户问题生成 SQL 查询
        
        Args:
            question: 用户的自然语言问题
        
        Returns:
            SQL 查询语句，如果生成失败返回 None
        
        知识点：
        --------
        1. 使用 PromptTemplate.format() 填充变量
        2. LLM 的 invoke() 方法发送请求并获取响应
        3. 使用正则表达式提取 SQL 语句
        """
        logger.info(f"生成 SQL，问题: {question}")
        
        # 获取日期上下文
        date_context = self._get_date_context()
        
        # 构建完整提示
        full_prompt = self.prompt.format(
            question=question,
            **date_context
        )
        
        try:
            # 调用 LLM
            response = self.llm.invoke(full_prompt)
            sql = self._extract_sql(response.content)
            
            if sql:
                logger.info(f"生成的 SQL: {sql}")
                return sql
            else:
                logger.warning(f"无法提取 SQL，原始响应: {response.content}")
                return None
                
        except Exception as e:
            logger.error(f"SQL 生成失败: {e}")
            return None
    
    def _extract_sql(self, text: str) -> Optional[str]:
        """
        从 LLM 响应中提取 SQL 语句
        
        Args:
            text: LLM 返回的文本
        
        Returns:
            提取的 SQL 语句
        
        知识点：
        --------
        LLM 可能返回的格式：
        1. 纯 SQL 语句
        2. 包含在 ```sql ... ``` 代码块中
        3. 包含额外解释文字
        
        需要使用正则表达式提取纯 SQL 部分。
        """
        # 尝试从代码块中提取
        sql_block_pattern = r"```sql\s*(.*?)\s*```"
        match = re.search(sql_block_pattern, text, re.DOTALL | re.IGNORECASE)
        if match:
            return match.group(1).strip()
        
        # 尝试提取 SELECT 语句
        select_pattern = r"(SELECT\s+.*?)(?:;|$)"
        match = re.search(select_pattern, text, re.DOTALL | re.IGNORECASE)
        if match:
            sql = match.group(1).strip()
            # 移除可能的尾部注释
            sql = re.sub(r"--.*$", "", sql, flags=re.MULTILINE)
            return sql.strip()
        
        # 如果都没匹配到，返回清理后的原文
        cleaned = text.strip()
        if cleaned.upper().startswith("SELECT"):
            return cleaned
        
        return None
    
    def validate_sql(self, sql: str) -> bool:
        """
        验证 SQL 语句的安全性
        
        Args:
            sql: SQL 语句
        
        Returns:
            是否安全
        
        知识点：
        --------
        SQL 注入防护：
        - 只允许 SELECT 语句
        - 禁止 DROP、DELETE、UPDATE、INSERT 等危险操作
        - 禁止多语句执行（分号分隔）
        """
        sql_upper = sql.upper()
        
        # 检查是否是 SELECT 语句
        if not sql_upper.strip().startswith("SELECT"):
            logger.warning(f"拒绝非 SELECT 语句: {sql}")
            return False
        
        # 检查是否包含危险关键字
        dangerous_keywords = ["DROP", "DELETE", "UPDATE", "INSERT", "ALTER", "TRUNCATE", "CREATE"]
        for keyword in dangerous_keywords:
            if keyword in sql_upper:
                logger.warning(f"SQL 包含危险关键字 {keyword}: {sql}")
                return False
        
        # 检查是否有多语句（分号分隔）
        # 允许 SQL 末尾的分号
        sql_no_trailing = sql.rstrip().rstrip(";")
        if ";" in sql_no_trailing:
            logger.warning(f"SQL 包含多语句: {sql}")
            return False
        
        return True


if __name__ == "__main__":
    # 测试 SQL 生成
    import colorlog
    
    # 配置彩色日志
    handler = colorlog.StreamHandler()
    handler.setFormatter(colorlog.ColoredFormatter(
        '%(log_color)s%(levelname)s: %(message)s'
    ))
    logging.getLogger().addHandler(handler)
    logging.getLogger().setLevel(logging.INFO)
    
    print("=" * 50)
    print("测试 SQL 生成器")
    print("=" * 50)
    
    generator = SQLGenerator()
    
    # 测试问题列表
    test_questions = [
        "北京明天天气怎么样？",
        "上海到北京的火车票",
        "天气",
        "近三天广州的天气预报",
    ]
    
    for question in test_questions:
        print(f"\n问题: {question}")
        sql = generator.generate_sql(question)
        if sql:
            print(f"SQL: {sql}")
            print(f"安全性: {'通过' if generator.validate_sql(sql) else '不通过'}")
        else:
            print("生成失败")
    
    print("\n" + "=" * 50)
