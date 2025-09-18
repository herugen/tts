"""
测试配置文件
提供测试用的fixtures和基础设置
"""

import pytest
import asyncio
import tempfile
import os
import sqlite3
from fastapi.testclient import TestClient
from fastapi import FastAPI
from app.main import app as main_app
from app.db_conn import startup, shutdown
from app.infra.queue import start_queue, stop_queue
from app.infra.repositories import TtsJobRepository, VoiceRepository, UploadRepository
from app.models import oc8r
import uuid
from datetime import datetime
from app.middleware import http_exception_handler, validation_exception_handler, general_exception_handler
from fastapi.exceptions import RequestValidationError
from fastapi import HTTPException
from app.api import health, uploads, queue, voices, jobs

@pytest.fixture(scope="session")
def event_loop():
    """创建事件循环"""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

@pytest.fixture(scope="function")
def test_db():
    """创建测试数据库"""
    # 创建临时数据库文件
    temp_db = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
    temp_db.close()
    
    # 设置测试数据库路径
    original_db_path = "data/tts.db"
    test_db_path = temp_db.name
    
    # 创建测试数据库连接
    conn = sqlite3.connect(test_db_path, check_same_thread=False)
    
    # 初始化表结构
    conn.execute("""
        CREATE TABLE IF NOT EXISTS uploads (
            id TEXT PRIMARY KEY,
            fileName TEXT NOT NULL,
            contentType TEXT NOT NULL,
            sizeBytes INTEGER NOT NULL,
            durationSeconds REAL,
            createdAt TEXT NOT NULL
        )
    """)
    
    conn.execute("""
        CREATE TABLE IF NOT EXISTS voices (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL UNIQUE,
            description TEXT,
            uploadId TEXT NOT NULL,
            createdAt TEXT NOT NULL,
            updatedAt TEXT NOT NULL,
            FOREIGN KEY (uploadId) REFERENCES uploads (id)
        )
    """)
    
    conn.execute("""
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
    """)
    
    conn.commit()
    
    yield conn
    
    # 清理
    conn.close()
    os.unlink(test_db_path)

@pytest.fixture(scope="function")
def test_app():
    """创建测试专用的FastAPI应用实例"""
    # 创建测试应用，不包含队列相关的启动/关闭钩子
    test_app = FastAPI()
    
    # 注册错误处理中间件
    test_app.add_exception_handler(HTTPException, http_exception_handler)
    test_app.add_exception_handler(RequestValidationError, validation_exception_handler)
    test_app.add_exception_handler(Exception, general_exception_handler)
    
    # 注册路由
    test_app.include_router(health.router, prefix="/api/v1")
    test_app.include_router(uploads.router, prefix="/api/v1")
    test_app.include_router(queue.router, prefix="/api/v1")
    test_app.include_router(voices.router, prefix="/api/v1")
    test_app.include_router(jobs.router, prefix="/api/v1")
    
    return test_app

@pytest.fixture(scope="function")
def test_client(test_app, test_db):
    """创建测试客户端"""
    # 临时替换数据库连接
    import app.db_conn as db_conn_module
    db_conn_module.db_conn = test_db
    
    with TestClient(test_app) as client:
        yield client

@pytest.fixture(scope="function")
async def test_queue():
    """创建测试队列"""
    await start_queue()
    yield
    await stop_queue()

@pytest.fixture
def sample_upload():
    """创建示例上传记录"""
    return oc8r.Upload(
        id=str(uuid.uuid4()),
        fileName="test.wav",
        contentType="audio/wav",
        sizeBytes=1024,
        durationSeconds=1.5,
        createdAt=datetime.now().isoformat()
    )

@pytest.fixture
def sample_voice(sample_upload):
    """创建示例音色记录"""
    return oc8r.Voice(
        id=str(uuid.uuid4()),
        name="Test Voice",
        description="Test voice description",
        uploadId=sample_upload.id,
        createdAt=datetime.now().isoformat(),
        updatedAt=datetime.now().isoformat()
    )

@pytest.fixture
def sample_tts_job():
    """创建示例TTS任务"""
    return oc8r.TtsJob(
        id=str(uuid.uuid4()),
        type=oc8r.Type.tts,
        status=oc8r.JobStatus.queued,
        createdAt=datetime.now().isoformat(),
        updatedAt=datetime.now().isoformat(),
        request=oc8r.CreateTtsJobRequest(
            text="Hello world",
            mode=oc8r.TtsMode.speaker,
            voiceId="test-voice-id"
        ),
        result=None,
        error=None
    )

@pytest.fixture
def sample_audio_file():
    """创建示例音频文件"""
    # 创建一个简单的WAV文件头（44字节）
    wav_header = b'RIFF\x24\x00\x00\x00WAVEfmt \x10\x00\x00\x00\x01\x00\x01\x00\x44\xac\x00\x00\x88X\x01\x00\x02\x00\x10\x00data\x00\x00\x00\x00'
    return wav_header
