# 第四章：LLM 与 SQL 生成

## 学习目标

- 理解 LLM（大语言模型）的基本概念
- 掌握 LangChain 框架的使用
- 学会 Prompt Engineering（提示工程）技术

## 1. 大语言模型（LLM）

### 什么是 LLM？

LLM（Large Language Model）是经过海量文本训练的 AI 模型，具备：
- 自然语言理解
- 文本生成
- 推理能力
- 代码生成

### 常见 LLM

| 模型 | 提供商 | 特点 |
|------|--------|------|
| GPT-4 | OpenAI | 综合能力强 |
| Claude | Anthropic | 安全性好 |
| Qwen | 阿里 | 中文优秀 |
| DeepSeek | DeepSeek | 代码能力强 |

## 2. LangChain 框架

LangChain 是 LLM 应用开发框架，提供：
- 统一的模型接口
- Prompt 模板管理
- 链式调用
- Agent 工具集成

### 基本使用

```python
from langchain_openai import ChatOpenAI

# 创建模型实例
llm = ChatOpenAI(
    api_key="your_key",
    base_url="https://api.openai.com/v1",
    model="gpt-4",
    temperature=0  # 0=确定性输出，1=随机性高
)

# 调用模型
response = llm.invoke("你好，请介绍一下自己。")
print(response.content)
```

## 3. Prompt Engineering

### 什么是 Prompt？

Prompt 是发送给 LLM 的指令文本。好的 Prompt 可以：
- 引导模型输出特定格式
- 提高回答准确性
- 减少幻觉（编造内容）

### Prompt 设计原则

1. **明确任务**：清楚说明要做什么
2. **提供示例**：Few-shot Learning
3. **限定格式**：要求特定输出格式
4. **设定角色**：让模型扮演专家

### SQL 生成 Prompt 示例

```python
SQL_PROMPT = """你是一个 SQL 生成助手。根据用户问题生成 MySQL 查询。

### 数据表
- weather_data: city, fx_date, temp_max, temp_min, text_day

### 示例
问题: 北京明天天气
SQL: SELECT * FROM weather_data WHERE city = '北京' AND fx_date = '2025-01-13'

### 要求
- 只输出 SQL 语句
- 使用 SELECT 语句

### 用户问题
{question}

### SQL:
"""
```

## 4. SQL 生成实现

```python
from langchain.prompts import PromptTemplate

class SQLGenerator:
    def __init__(self):
        self.llm = ChatOpenAI(temperature=0)
        self.prompt = PromptTemplate(
            input_variables=["question"],
            template=SQL_PROMPT
        )
    
    def generate(self, question: str) -> str:
        # 填充模板
        full_prompt = self.prompt.format(question=question)
        
        # 调用 LLM
        response = self.llm.invoke(full_prompt)
        
        # 提取 SQL
        return self._extract_sql(response.content)
    
    def _extract_sql(self, text: str) -> str:
        """从回复中提取 SQL 语句"""
        import re
        match = re.search(r"SELECT.*", text, re.IGNORECASE | re.DOTALL)
        return match.group() if match else ""
```

## 5. 安全验证

生成的 SQL 必须经过安全检查：

```python
def validate_sql(self, sql: str) -> bool:
    # 只允许 SELECT
    if not sql.upper().startswith("SELECT"):
        return False
    
    # 禁止危险关键字
    dangerous = ["DROP", "DELETE", "UPDATE", "INSERT"]
    for keyword in dangerous:
        if keyword in sql.upper():
            return False
    
    return True
```

## 知识点总结

| 概念 | 说明 |
|------|------|
| LLM | 大语言模型 |
| LangChain | LLM 应用框架 |
| Prompt | 发送给模型的指令 |
| Temperature | 控制输出随机性 |
| Few-shot | 在 Prompt 中提供示例 |

## 下一步

继续学习 [第五章：MCP 协议详解](05_MCP协议详解.md)
