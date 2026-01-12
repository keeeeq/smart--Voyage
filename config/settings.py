# -*- coding: utf-8 -*-
"""
配置管理模块
============
使用 pydantic-settings 从 .env 文件加载配置。

知识点：
--------
1. pydantic-settings 是 Pydantic 的扩展，专门用于管理应用配置
2. BaseSettings 会自动从环境变量或 .env 文件读取值
3. 使用 Field 可以设置默认值和字段描述
4. model_config 用于配置 .env 文件路径和编码
"""

from pathlib import Path
from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    """
    应用配置类
    
    所有配置项都可以通过环境变量或 .env 文件设置。
    环境变量名称与字段名称对应（不区分大小写）。
    """
    
    # ========== MySQL 数据库配置 ==========
    mysql_host: str = Field(default="localhost", description="MySQL 主机地址")
    mysql_port: int = Field(default=3306, description="MySQL 端口")
    mysql_user: str = Field(default="root", description="MySQL 用户名")
    mysql_password: str = Field(default="root", description="MySQL 密码")
    mysql_database: str = Field(default="smart_voyage", description="数据库名称")
    
    # ========== OpenAI 兼容 API 配置 ==========
    openai_api_key: str = Field(default="", description="OpenAI API Key")
    openai_base_url: str = Field(
        default="https://api.openai.com/v1", 
        description="OpenAI API Base URL (支持兼容接口)"
    )
    openai_model: str = Field(default="gpt-4", description="使用的模型名称")
    
    # ========== 和风天气 API 配置 ==========
    qweather_api_key: str = Field(default="", description="和风天气 API Key")
    qweather_base_url: str = Field(
        default="https://devapi.qweather.com/v7",
        description="和风天气 API Base URL"
    )
    
    # ========== 服务配置 ==========
    mcp_server_port: int = Field(default=8000, description="MCP 服务端口")
    a2a_server_port: int = Field(default=8001, description="A2A 服务端口")
    
    # ========== Pydantic 配置 ==========
    model_config = {
        # .env 文件路径（相对于项目根目录）
        "env_file": Path(__file__).parent.parent / ".env",
        "env_file_encoding": "utf-8",
        # 环境变量不区分大小写
        "case_sensitive": False,
        # 允许从环境变量读取额外字段
        "extra": "ignore",
    }
    
    @property
    def mysql_connection_string(self) -> str:
        """
        返回 MySQL 连接字符串
        
        Returns:
            str: 格式为 mysql+connector://user:password@host:port/database
        """
        return (
            f"mysql+connector://{self.mysql_user}:{self.mysql_password}"
            f"@{self.mysql_host}:{self.mysql_port}/{self.mysql_database}"
        )


# 创建全局配置实例（单例模式）
# 导入此模块时会自动加载 .env 文件
settings = Settings()


if __name__ == "__main__":
    # 测试配置加载
    print("=" * 50)
    print("SmartVoyage 配置信息")
    print("=" * 50)
    print(f"MySQL: {settings.mysql_host}:{settings.mysql_port}")
    print(f"Database: {settings.mysql_database}")
    print(f"LLM Model: {settings.openai_model}")
    print(f"LLM Base URL: {settings.openai_base_url}")
    print(f"QWeather API: {'已配置' if settings.qweather_api_key else '未配置'}")
    print("=" * 50)
