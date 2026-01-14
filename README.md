# SmartVoyage 智能旅行助手

<div align="center">

![Python](https://img.shields.io/badge/Python-3.12-blue)
![LangChain](https://img.shields.io/badge/LangChain-0.3-green)
![FastMCP](https://img.shields.io/badge/FastMCP-1.0-purple)
![A2A](https://img.shields.io/badge/A2A-Protocol-orange)
![Streamlit](https://img.shields.io/badge/Streamlit-1.47-red)

**基于 MCP + A2A 协议的分布式智能旅行助手系统**

</div>

## 📖 项目简介

SmartVoyage 是一个智能旅行助手系统，采用分布式微服务架构。系统利用大语言模型（LLM）、MCP（模型上下文协议）和 A2A（代理间通信协议）实现多 Agent 协作处理用户查询。

### ✨ 核心功能

| 功能 | 描述 |
|------|------|
| 🌤️ 天气查询 | 查询全国主要城市的天气预报 |
| 🚄 火车票查询 | 查询火车班次、票价、余票信息 |
| ✈️ 机票查询 | 查询航班信息和票价 |
| 🎤 演唱会查询 | 查询演出信息和票务 |

### 🏗️ 分布式架构

```
                 Streamlit 前端 (:8502)
                         ↓
┌──────────────────────────────────────────────────────┐
│                   API 网关 (:8000)                    │
│            意图识别 → Agent 路由 → 结果润色            │
└──────────────────────────────────────────────────────┘
                         ↓ A2A Protocol
┌──────────────────────────────────────────────────────┐
│                 A2A Agent Server 层                   │
│  ┌────────────┐ ┌────────────┐ ┌────────────┐        │
│  │ A2A天气    │ │ A2A票务    │ │ A2A订票    │        │
│  │  :5005     │ │  :5006     │ │  :5007     │        │
│  └────────────┘ └────────────┘ └────────────┘        │
└──────────────────────────────────────────────────────┘
                         ↓ MCP Protocol
┌──────────────────────────────────────────────────────┐
│                   MCP Server 层                       │
│  ┌────────────┐ ┌────────────┐ ┌────────────┐        │
│  │ MCP天气    │ │ MCP票务    │ │ MCP订票    │        │
│  │  :8002     │ │  :8001     │ │  :8003     │        │
│  └────────────┘ └────────────┘ └────────────┘        │
└──────────────────────────────────────────────────────┘
                         ↓
                    MySQL 数据库
```


## 🚀 快速开始

### 1. 环境准备

```bash
# 创建虚拟环境
conda create -n agent python=3.12
conda activate agent

# 安装依赖
pip install -r requirements.txt
```

### 2. 配置环境变量

编辑 `.env` 文件：

```bash
# MySQL 数据库配置
MYSQL_HOST=localhost
MYSQL_PORT=3306
MYSQL_USER=root
MYSQL_PASSWORD=your_password
MYSQL_DATABASE=smart_voyage

# LLM API 配置
OPENAI_API_KEY=your_api_key
OPENAI_BASE_URL=https://api.openai.com/v1
OPENAI_MODEL=gpt-4
```

### 3. 初始化数据库

```bash
# 创建数据库和表
mysql -u root -p < database/init_db.sql

# 插入测试数据
python database/insert_test_data.py
```

### 4. 一键启动

**方式1：双击启动脚本**
```
start_a2a.bat
```

**方式2：PyCharm 运行配置**
- 选择 `🚀 启动全部服务` 运行配置

**方式3：手动启动**
```bash
# 启动 MCP Server（3个终端）
python mcp_server/mcp_weather_server.py   # :8002
python mcp_server/mcp_ticket_server.py    # :8001
python mcp_server/mcp_order_server.py     # :8003

# 启动 A2A Agent（3个终端）
python a2a_server/weather_server.py       # :5005
python a2a_server/ticket_server.py        # :5006
python a2a_server/order_server.py         # :5007

# 启动前端
streamlit run streamlit_app_a2a.py        # :8502
```

### 5. 访问应用

- **Streamlit 前端**: http://localhost:8502

## 📁 项目结构

```
SmartVoyage/
├── .env                      # 环境配置
├── README.md                 # 本文件
├── requirements.txt          # 依赖清单
├── start_a2a.bat            # Windows 启动脚本
├── start_all_services.py    # Python 启动脚本
├── streamlit_app_a2a.py     # Streamlit 前端
├── smart_voyage_main.py     # 命令行客户端
├── main_prompts.py          # LLM 提示词管理
│
├── config/                   # 配置模块
│   └── settings.py          # Pydantic 配置
│
├── database/                 # 数据库模块
│   ├── init_db.sql          # 初始化脚本
│   ├── insert_test_data.py  # 测试数据
│   └── connection.py        # 连接管理
│
├── mcp_server/              # MCP 服务层
│   ├── mcp_weather_server.py  # 天气 MCP (:8002)
│   ├── mcp_ticket_server.py   # 票务 MCP (:8001)
│   └── mcp_order_server.py    # 订票 MCP (:8003)
│
├── a2a_server/              # A2A Agent 层
│   ├── weather_server.py    # 天气 Agent (:5005)
│   ├── ticket_server.py     # 票务 Agent (:5006)
│   └── order_server.py      # 订票 Agent (:5007)
│
├── llm/                     # LLM 模块
├── crawler/                 # 爬虫模块
├── doc/                     # 学习文档
└── tests/                   # 测试模块
```

## 💬 使用示例

### 天气查询
```
用户: 北京今天天气怎么样？
助手: 北京今天天气晴，温度 -3~5°C，湿度 35%，北风。
```

### 火车票查询
```
用户: 北京到上海的火车票
助手: 【北京 → 上海 火车票】
      G1: 07:00-11:36 (4h36m), 二等座¥553
      G3: 08:00-12:40 (4h40m), 二等座¥553
```

## 🔧 技术栈

| 技术 | 用途 |
|------|------|
| LangChain | LLM 框架，SQL 生成和意图识别 |
| FastMCP | MCP 协议实现 |
| python-a2a | A2A 协议实现 |
| MySQL | 数据存储 |
| Streamlit | 前端界面 |

## 📚 学习文档

位于 `doc/` 目录：

1. [项目结构与环境搭建](doc/01_项目结构与环境搭建.md)
2. [数据库设计与连接](doc/02_数据库设计与连接.md)
3. [天气爬虫实现](doc/03_天气爬虫实现.md)
4. [LLM 与 SQL 生成](doc/04_LLM与SQL生成.md)
5. [MCP 协议详解](doc/05_MCP协议详解.md)
6. [A2A 协议详解](doc/06_A2A协议详解.md)
7. [Streamlit 前端](doc/07_Streamlit前端.md)

## 📄 许可证

MIT License
