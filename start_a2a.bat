@echo off
chcp 65001
echo ====================================================
echo SmartVoyage 分布式服务一键启动脚本
echo ====================================================
echo.

REM 设置项目目录
set PROJECT_DIR=%~dp0
cd /d %PROJECT_DIR%

echo 正在启动 8 个服务...
echo.

REM 1. MCP 服务层
echo [1/8] 启动 MCP 天气服务器 (8002)...
start "MCP-Weather-8002" cmd /k "conda activate agent && python mcp_server/mcp_weather_server.py"
timeout /t 2 /nobreak >nul

echo [2/8] 启动 MCP 票务服务器 (8001)...
start "MCP-Ticket-8001" cmd /k "conda activate agent && python mcp_server/mcp_ticket_server.py"
timeout /t 2 /nobreak >nul

echo [3/8] 启动 MCP 订票服务器 (8003)...
start "MCP-Order-8003" cmd /k "conda activate agent && python mcp_server/mcp_order_server.py"
timeout /t 2 /nobreak >nul

REM 2. A2A Agent 层
echo [4/8] 启动 A2A 天气 Agent (5005)...
start "A2A-Weather-5005" cmd /k "conda activate agent && python a2a_server/weather_server.py"
timeout /t 2 /nobreak >nul

echo [5/8] 启动 A2A 票务 Agent (5006)...
start "A2A-Ticket-5006" cmd /k "conda activate agent && python a2a_server/ticket_server.py"
timeout /t 2 /nobreak >nul

echo [6/8] 启动 A2A 订票 Agent (5007)...
start "A2A-Order-5007" cmd /k "conda activate agent && python a2a_server/order_server.py"
timeout /t 3 /nobreak >nul

REM 3. API 网关
echo [7/8] 启动 API 网关 (8000)...
start "API-Gateway-8000" cmd /k "conda activate agent && python api_gateway.py"
timeout /t 3 /nobreak >nul

REM 4. 前端
echo [8/8] 启动 Streamlit 前端 (8502)...
start "Streamlit-8502" cmd /k "conda activate agent && streamlit run streamlit_app_a2a.py --server.port 8502"

echo.
echo ====================================================
echo 全部服务已启动！
echo ====================================================
echo.
echo 服务列表:
echo   - MCP 天气:    http://127.0.0.1:8002/mcp
echo   - MCP 票务:    http://127.0.0.1:8001/mcp
echo   - MCP 订票:    http://127.0.0.1:8003/mcp
echo   - A2A 天气:    http://127.0.0.1:5005
echo   - A2A 票务:    http://127.0.0.1:5006
echo   - A2A 订票:    http://127.0.0.1:5007
echo   - API 网关:    http://127.0.0.1:8000
echo   - API 文档:    http://127.0.0.1:8000/docs
echo   - 前端界面:    http://127.0.0.1:8502
echo.
echo 按任意键打开浏览器...
pause >nul

start http://localhost:8502
