# -*- coding: utf-8 -*-
"""
数据库连接管理模块
==================
封装 MySQL 数据库连接和查询操作。

知识点：
--------
1. mysql-connector-python 是 MySQL 官方的 Python 驱动
2. 连接池（Connection Pool）可以复用数据库连接，提高性能
3. 使用 with 语句（上下文管理器）确保连接正确关闭
4. 参数化查询（%s 占位符）可以防止 SQL 注入攻击
"""

import json
import logging
from typing import List, Dict, Any, Optional
from contextlib import contextmanager
from datetime import datetime, date

import mysql.connector
from mysql.connector import pooling, Error as MySQLError

# 导入配置
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))
from config import settings

# 配置日志
logger = logging.getLogger(__name__)


class DateTimeEncoder(json.JSONEncoder):
    """
    自定义 JSON 编码器，处理 datetime 和 date 类型
    
    知识点：
    --------
    Python 的 json 模块默认不支持序列化 datetime 对象，
    需要自定义编码器将其转换为字符串。
    """
    def default(self, obj):
        if isinstance(obj, datetime):
            return obj.strftime("%Y-%m-%d %H:%M:%S")
        elif isinstance(obj, date):
            return obj.strftime("%Y-%m-%d")
        return super().default(obj)


class DatabaseConnection:
    """
    数据库连接管理类
    
    使用连接池管理数据库连接，支持查询和执行 SQL 语句。
    
    知识点：
    --------
    连接池的优势：
    - 减少创建/销毁连接的开销
    - 限制最大连接数，保护数据库
    - 自动管理连接的生命周期
    """
    
    _pool: Optional[pooling.MySQLConnectionPool] = None
    
    @classmethod
    def init_pool(cls, pool_size: int = 5) -> None:
        """
        初始化数据库连接池
        
        Args:
            pool_size: 连接池大小，默认 5 个连接
            
        知识点：
        --------
        连接池大小的选择：
        - 太小：请求可能需要等待可用连接
        - 太大：浪费数据库资源
        - 一般建议：CPU 核心数 * 2 + 1
        """
        if cls._pool is None:
            try:
                cls._pool = pooling.MySQLConnectionPool(
                    pool_name="smart_voyage_pool",
                    pool_size=pool_size,
                    pool_reset_session=True,  # 归还连接时重置会话状态
                    host=settings.mysql_host,
                    port=settings.mysql_port,
                    user=settings.mysql_user,
                    password=settings.mysql_password,
                    database=settings.mysql_database,
                    charset="utf8mb4",  # 支持 emoji 等特殊字符
                    collation="utf8mb4_unicode_ci",
                    autocommit=True,  # 自动提交事务
                )
                logger.info(f"数据库连接池已初始化，大小: {pool_size}")
            except MySQLError as e:
                logger.error(f"初始化连接池失败: {e}")
                raise
    
    @classmethod
    @contextmanager
    def get_connection(cls):
        """
        获取数据库连接（上下文管理器）
        
        使用方法：
        ```python
        with DatabaseConnection.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM users")
        ```
        
        知识点：
        --------
        @contextmanager 装饰器可以将生成器函数转换为上下文管理器，
        yield 之前的代码在 __enter__ 时执行，
        yield 之后的代码在 __exit__ 时执行。
        """
        if cls._pool is None:
            cls.init_pool()
        
        conn = None
        try:
            conn = cls._pool.get_connection()
            yield conn
        except MySQLError as e:
            logger.error(f"数据库连接错误: {e}")
            raise
        finally:
            if conn and conn.is_connected():
                conn.close()  # 归还连接到池中
    
    @classmethod
    def execute_query(
        cls, 
        sql: str, 
        params: Optional[tuple] = None,
        as_dict: bool = True
    ) -> List[Dict[str, Any]]:
        """
        执行 SELECT 查询并返回结果
        
        Args:
            sql: SQL 查询语句
            params: 查询参数（可选），使用 %s 占位符
            as_dict: 是否返回字典格式（默认 True）
        
        Returns:
            查询结果列表
        
        Example:
            ```python
            results = DatabaseConnection.execute_query(
                "SELECT * FROM weather_data WHERE city = %s",
                ("北京",)
            )
            ```
        
        知识点：
        --------
        参数化查询的重要性：
        - 防止 SQL 注入攻击
        - 自动处理特殊字符转义
        - 提高查询性能（预编译）
        """
        with cls.get_connection() as conn:
            cursor = conn.cursor(dictionary=as_dict)
            try:
                cursor.execute(sql, params or ())
                results = cursor.fetchall()
                logger.debug(f"查询成功，返回 {len(results)} 条记录")
                return results
            except MySQLError as e:
                logger.error(f"查询执行失败: {e}\nSQL: {sql}")
                raise
            finally:
                cursor.close()
    
    @classmethod
    def execute_update(
        cls, 
        sql: str, 
        params: Optional[tuple] = None
    ) -> int:
        """
        执行 INSERT/UPDATE/DELETE 语句
        
        Args:
            sql: SQL 语句
            params: 参数（可选）
        
        Returns:
            受影响的行数
        """
        with cls.get_connection() as conn:
            cursor = conn.cursor()
            try:
                cursor.execute(sql, params or ())
                conn.commit()
                affected_rows = cursor.rowcount
                logger.debug(f"更新成功，影响 {affected_rows} 行")
                return affected_rows
            except MySQLError as e:
                conn.rollback()
                logger.error(f"更新执行失败: {e}\nSQL: {sql}")
                raise
            finally:
                cursor.close()
    
    @classmethod
    def execute_many(
        cls, 
        sql: str, 
        params_list: List[tuple]
    ) -> int:
        """
        批量执行 SQL 语句（高性能批量插入）
        
        Args:
            sql: SQL 语句模板
            params_list: 参数列表
        
        Returns:
            受影响的总行数
            
        知识点：
        --------
        executemany() 方法比循环调用 execute() 效率高很多，
        因为它只需要一次网络往返就能执行多条语句。
        """
        with cls.get_connection() as conn:
            cursor = conn.cursor()
            try:
                cursor.executemany(sql, params_list)
                conn.commit()
                affected_rows = cursor.rowcount
                logger.debug(f"批量更新成功，影响 {affected_rows} 行")
                return affected_rows
            except MySQLError as e:
                conn.rollback()
                logger.error(f"批量更新失败: {e}")
                raise
            finally:
                cursor.close()
    
    @classmethod
    def query_to_json(cls, sql: str, params: Optional[tuple] = None) -> str:
        """
        执行查询并返回 JSON 字符串
        
        用于将查询结果传递给 LLM 进行分析。
        
        Args:
            sql: SQL 查询语句
            params: 查询参数
        
        Returns:
            JSON 格式的查询结果
        """
        results = cls.execute_query(sql, params)
        return json.dumps(results, ensure_ascii=False, cls=DateTimeEncoder, indent=2)


def get_db_connection():
    """
    获取数据库连接（便捷函数）
    
    Returns:
        上下文管理器，用于 with 语句
    """
    return DatabaseConnection.get_connection()


if __name__ == "__main__":
    # 测试数据库连接
    import colorlog
    
    # 配置彩色日志
    handler = colorlog.StreamHandler()
    handler.setFormatter(colorlog.ColoredFormatter(
        '%(log_color)s%(levelname)s:%(name)s:%(message)s'
    ))
    logging.getLogger().addHandler(handler)
    logging.getLogger().setLevel(logging.DEBUG)
    
    print("=" * 50)
    print("测试数据库连接")
    print("=" * 50)
    
    try:
        # 初始化连接池
        DatabaseConnection.init_pool()
        
        # 测试查询
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT 1 as test")
            result = cursor.fetchone()
            print(f"连接测试成功: {result}")
            cursor.close()
        
        print("=" * 50)
        print("数据库连接正常！")
        print("=" * 50)
    except Exception as e:
        print(f"连接失败: {e}")
        print("请检查 MySQL 服务是否启动，以及 .env 配置是否正确")
