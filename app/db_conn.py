"""
文件级注释：
本模块负责数据库连接管理，提供全局 SQLite 连接和依赖注入支持。

背景说明：
- 使用全局连接模式，适合 SQLite 单文件数据库场景
- 支持 FastAPI 依赖注入，简化各模块的数据库访问
- 统一数据库文件路径，避免数据分散

架构说明：
- 提供 startup/shutdown 钩子，确保连接生命周期管理
- get_db_conn 函数支持 FastAPI Depends 注入
- 所有模块统一使用此连接，保证数据一致性
"""

import sqlite3
import os
from typing import Optional

# 全局数据库连接
db_conn: Optional[sqlite3.Connection] = None


def get_db_conn() -> sqlite3.Connection:
    """
    获取全局数据库连接，用于 FastAPI Depends 注入

    Returns:
        sqlite3.Connection: 全局数据库连接

    Raises:
        RuntimeError: 如果数据库连接未初始化
    """
    if db_conn is None:
        raise RuntimeError("Database connection not initialized. Call startup() first.")
    return db_conn


async def startup():
    """
    应用启动时初始化数据库连接
    - 创建数据库目录（如果不存在）
    - 建立全局连接
    - 初始化数据库表结构
    """
    global db_conn

    # 确保数据库目录存在
    os.makedirs("data", exist_ok=True)

    # 建立全局连接
    db_conn = sqlite3.connect("data/tts.db", check_same_thread=False)

    # 初始化数据库表结构
    _init_database()


async def shutdown():
    """
    应用关闭时清理数据库连接
    """
    global db_conn
    if db_conn:
        db_conn.close()
        db_conn = None


def _init_database():
    """
    初始化数据库表结构
    """
    if db_conn is None:
        return

    # 创建上传记录表
    db_conn.execute(
        """
        CREATE TABLE IF NOT EXISTS uploads (
            id TEXT PRIMARY KEY,
            fileName TEXT NOT NULL,
            contentType TEXT NOT NULL,
            sizeBytes INTEGER NOT NULL,
            durationSeconds REAL,
            createdAt TEXT NOT NULL
        )
    """
    )

    # 创建语音记录表
    db_conn.execute(
        """
        CREATE TABLE IF NOT EXISTS voices (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL UNIQUE,
            description TEXT,
            uploadId TEXT NOT NULL,
            createdAt TEXT NOT NULL,
            updatedAt TEXT NOT NULL,
            FOREIGN KEY (uploadId) REFERENCES uploads (id)
        )
    """
    )

    # 创建 TTS 任务表
    db_conn.execute(
        """
        CREATE TABLE IF NOT EXISTS tts_jobs (
            id TEXT PRIMARY KEY,
            type TEXT NOT NULL,
            status TEXT NOT NULL,
            createdAt TEXT NOT NULL,
            updatedAt TEXT NOT NULL,
            request TEXT NOT NULL,
            result TEXT,
            error TEXT
        )
    """
    )

    db_conn.commit()
