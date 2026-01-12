# 第五章：MCP 协议详解

## 学习目标

- 理解 MCP（Model Context Protocol）协议
- 掌握 MCP Server 的实现方法
- 学会注册和调用 MCP 工具

## 1. MCP 协议简介

### 什么是 MCP？

MCP（Model Context Protocol）是由 Anthropic 开源的协议，用于：
- LLM 与外部工具的安全集成
- 标准化的工具调用接口
- 双向通信（请求/响应）

### MCP vs 传统函数调用

```
传统方式:
  用户 → LLM → 手动解析 → 调用函数 → 格式化结果 → 返回

MCP 方式:
  用户 → LLM ←→ MCP Server (工具) ← 自动处理
```

## 2. MCP 核心概念

### Tool（工具）

可被 LLM 调用的功能：

```python
Tool(
    name="query_weather",           # 工具名称
    description="查询城市天气",      # 描述（LLM 据此判断何时使用）
    inputSchema={                   # 输入参数定义
        "type": "object",
        "properties": {
            "city": {"type": "string", "description": "城市名"}
        },
        "required": ["city"]
    }
)
```

### Resource（资源）

可被读取的数据源（如数据库表、文件）。

### Prompt（提示）

预定义的提示模板。

## 3. MCP Server 实现

```python
from mcp.server import Server
from mcp.types import Tool, TextContent

# 创建服务器
server = Server("smart-voyage")

# 注册工具列表
@server.list_tools()
async def list_tools():
    return [
        Tool(
            name="query_weather",
            description="查询城市天气预报",
            inputSchema={
                "type": "object",
                "properties": {
                    "city": {"type": "string"}
                },
                "required": ["city"]
            }
        )
    ]

# 处理工具调用
@server.call_tool()
async def call_tool(name: str, arguments: dict):
    if name == "query_weather":
        city = arguments.get("city")
        # 查询数据库
        result = query_weather_from_db(city)
        return [TextContent(type="text", text=result)]
```

## 4. MCP 传输方式

### stdio（标准输入输出）

适合本地进程间通信：

```python
from mcp.server.stdio import stdio_server

async def run():
    async with stdio_server() as (read, write):
        await server.run(read, write, server.create_initialization_options())
```

### SSE（Server-Sent Events）

适合 HTTP 场景，单向服务器推送。

### WebSocket

适合需要双向实时通信的场景。

## 5. 与 LangChain 集成

使用 `langchain-mcp-adapters` 将 MCP 工具导入 LangChain：

```python
from langchain_mcp_adapters import MCPClient

# 连接 MCP Server
client = MCPClient("http://localhost:8000")

# 获取工具列表
tools = client.get_tools()

# 将工具绑定到 LLM
llm_with_tools = llm.bind_tools(tools)
```

## 知识点总结

| 概念 | 说明 |
|------|------|
| MCP | Model Context Protocol，LLM 工具集成协议 |
| Tool | MCP 中可被调用的功能 |
| inputSchema | 工具输入参数的 JSON Schema 定义 |
| stdio | 使用标准输入输出的传输方式 |

## 下一步

继续学习 [第六章：A2A 协议详解](06_A2A协议详解.md)
