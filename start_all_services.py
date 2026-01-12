# -*- coding: utf-8 -*-
"""
SmartVoyage 一键启动脚本 (Python 版)
======================================
在 PyCharm 中运行此脚本，自动启动所有 8 个服务。
"""

import subprocess
import sys
import time
import webbrowser
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent
CONDA_ENV = "agent"


def start_service(name: str, script: str, port: int):
    """启动单个服务"""
    print(f"[启动] {name} (:{port})...")
    cmd = f'start "{name}-{port}" cmd /k "cd /d {PROJECT_ROOT} && conda activate {CONDA_ENV} && python {script}"'
    subprocess.Popen(cmd, shell=True)
    time.sleep(1.5)
    print(f"  ✓ {name}")


def start_streamlit():
    """启动 Streamlit"""
    print(f"[启动] Streamlit (:8502)...")
    cmd = f'start "Streamlit-8502" cmd /k "cd /d {PROJECT_ROOT} && conda activate {CONDA_ENV} && streamlit run streamlit_app_a2a.py --server.port 8502"'
    subprocess.Popen(cmd, shell=True)
    print(f"  ✓ Streamlit")


def main():
    print("=" * 50)
    print("  SmartVoyage 分布式服务启动")
    print("=" * 50)
    print()
    
    # MCP 层
    print("【MCP Server 层】")
    start_service("MCP天气", "mcp_server/mcp_weather_server.py", 8002)
    start_service("MCP票务", "mcp_server/mcp_ticket_server.py", 8001)
    start_service("MCP订票", "mcp_server/mcp_order_server.py", 8003)
    
    print()
    print("等待 MCP 就绪...")
    time.sleep(2)
    
    # A2A 层
    print()
    print("【A2A Agent 层】")
    start_service("A2A天气", "a2a_server/weather_server.py", 5005)
    start_service("A2A票务", "a2a_server/ticket_server.py", 5006)
    start_service("A2A订票", "a2a_server/order_server.py", 5007)
    
    print()
    print("等待 Agent 就绪...")
    time.sleep(2)
    
    # API 网关
    print()
    print("【API 网关】")
    start_service("API网关", "api_gateway.py", 8000)
    
    print()
    print("等待网关就绪...")
    time.sleep(2)
    
    # 前端
    print()
    print("【前端】")
    start_streamlit()
    
    print()
    print("=" * 50)
    print("  ✅ 全部 8 个服务已启动！")
    print("=" * 50)
    print()
    print("  服务列表:")
    print("  ├─ MCP天气:  http://127.0.0.1:8002")
    print("  ├─ MCP票务:  http://127.0.0.1:8001")
    print("  ├─ MCP订票:  http://127.0.0.1:8003")
    print("  ├─ A2A天气:  http://127.0.0.1:5005")
    print("  ├─ A2A票务:  http://127.0.0.1:5006")
    print("  ├─ A2A订票:  http://127.0.0.1:5007")
    print("  ├─ API网关:  http://127.0.0.1:8000")
    print("  ├─ API文档:  http://127.0.0.1:8000/docs")
    print("  └─ 前端:     http://127.0.0.1:8502")
    print()
    
    time.sleep(3)
    print("正在打开浏览器...")
    webbrowser.open("http://localhost:8502")
    
    print("关闭各窗口可停止服务。")


if __name__ == "__main__":
    main()
