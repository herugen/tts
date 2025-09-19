"""
测试配置文件
提供测试用的fixtures和基础设置

- 使用应用服务容器管理所有服务
- 支持依赖注入和mock测试
- 遵循分层架构原则
- 提供完整的测试环境设置
"""

import pytest
import asyncio
import tempfile
import os
import sqlite3
from unittest.mock import Mock, AsyncMock
from fastapi.testclient import TestClient
from fastapi import FastAPI
from app.infra.repositories import TtsJobRepository, VoiceRepository, UploadRepository
from app.infra.storage import LocalFileStorage
from app.infra.indextts_client import IndexTtsClient
from app.models import oc8r
from app.container import ApplicationContainer
from app.application.tts_service import TtsService
from app.application.voice_service import VoiceService
from app.application.upload_service import UploadService
from app.application.queue_service import QueueService
from app.application.audio_service import AudioService
from app.application.tts_processor import TtsTaskProcessor
from app.application.file_service import FileService
import uuid
from datetime import datetime
from app.middleware import (
    http_exception_handler,
    validation_exception_handler,
    general_exception_handler,
)
from fastapi.exceptions import RequestValidationError
from fastapi import HTTPException
from app.api import health, uploads, queue, voices, jobs, audio


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
    temp_db = tempfile.NamedTemporaryFile(delete=False, suffix=".db")
    temp_db.close()

    # 设置测试数据库路径
    test_db_path = temp_db.name

    # 创建测试数据库连接
    conn = sqlite3.connect(test_db_path, check_same_thread=False)

    # 初始化表结构
    conn.execute(
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

    conn.execute(
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

    conn.execute(
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
    test_app.include_router(audio.router, prefix="/api/v1")

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
def test_container(test_db):
    """创建测试应用服务容器"""
    # 创建测试容器实例
    container = ApplicationContainer()

    # 清理现有服务
    container.clear_services()

    yield container

    # 测试后清理
    container.clear_services()


@pytest.fixture(scope="function")
def mock_queue_manager():
    """创建模拟队列管理器"""
    mock_manager = Mock()
    mock_manager.enqueue = AsyncMock(return_value="test-job-id")
    mock_manager.cancel = AsyncMock()
    mock_manager.running_job_id = Mock(return_value=None)
    mock_manager.queue_length = Mock(return_value=0)
    return mock_manager


@pytest.fixture(scope="function")
def mock_storage():
    """创建模拟文件存储"""
    mock_storage = Mock(spec=LocalFileStorage)
    mock_storage.save_upload = Mock(
        return_value=("test-file-id", "/test/path", "audio/wav", 1024)
    )
    mock_storage.get_file_path = Mock(return_value="/test/path")
    mock_storage.delete_file = Mock()
    return mock_storage


@pytest.fixture(scope="function")
def mock_indextts_client():
    """创建模拟IndexTTS客户端"""
    mock_client = Mock(spec=IndexTtsClient)
    mock_client.synthesize = AsyncMock(return_value=b"mock audio data")
    return mock_client


@pytest.fixture(scope="function")
def tts_service_fixture(test_db, mock_queue_manager):
    """创建测试TTS应用服务"""
    job_repo = TtsJobRepository(test_db)
    voice_repo = VoiceRepository(test_db)
    return TtsService(job_repo, voice_repo, mock_queue_manager)


@pytest.fixture(scope="function")
def voice_service_fixture(test_db, mock_storage):
    """创建测试Voice应用服务"""
    voice_repo = VoiceRepository(test_db)
    upload_repo = UploadRepository(test_db)
    return VoiceService(voice_repo, mock_storage, upload_repo)


@pytest.fixture(scope="function")
def upload_service_fixture(mock_storage):
    """创建测试Upload应用服务"""
    return UploadService(mock_storage)


@pytest.fixture(scope="function")
def queue_service_fixture(mock_queue_manager, tts_processor_fixture):
    """创建测试Queue应用服务"""
    return QueueService(mock_queue_manager, tts_processor_fixture)


@pytest.fixture(scope="function")
def audio_service_fixture(mock_storage):
    """创建测试Audio应用服务"""
    return AudioService(mock_storage)


@pytest.fixture(scope="function")
def tts_processor_fixture(test_db, mock_storage, mock_indextts_client):
    """创建测试TTS任务处理器"""
    voice_repo = VoiceRepository(test_db)
    upload_repo = UploadRepository(test_db)
    file_service = FileService(mock_storage)
    return TtsTaskProcessor(
        voice_repo, upload_repo, mock_storage, mock_indextts_client, file_service
    )


@pytest.fixture(scope="function")
def file_service_fixture(mock_storage):
    """创建测试文件处理服务"""
    return FileService(mock_storage)


@pytest.fixture(scope="function")
def mock_dependencies():
    """创建模拟依赖注入函数"""

    def mock_get_tts_service():
        return Mock(spec=TtsService)

    def mock_get_voice_service():
        return Mock(spec=VoiceService)

    def mock_get_upload_service():
        return Mock(spec=UploadService)

    def mock_get_queue_service():
        return Mock(spec=QueueService)

    def mock_get_audio_service():
        return Mock(spec=AudioService)

    def mock_get_tts_processor():
        return Mock(spec=TtsTaskProcessor)

    return {
        "get_tts_service": mock_get_tts_service,
        "get_voice_service": mock_get_voice_service,
        "get_upload_service": mock_get_upload_service,
        "get_queue_service": mock_get_queue_service,
        "get_audio_service": mock_get_audio_service,
        "get_tts_processor": mock_get_tts_processor,
    }


@pytest.fixture(scope="function")
def test_client_with_mocks(test_app, test_db, mock_dependencies):
    """创建带有模拟依赖的测试客户端"""
    # 临时替换数据库连接
    import app.db_conn as db_conn_module

    db_conn_module.db_conn = test_db

    # 模拟依赖注入
    import app.dependencies as deps_module

    original_get_tts_service = deps_module.get_tts_service
    original_get_voice_service = deps_module.get_voice_service
    original_get_upload_service = deps_module.get_upload_service
    original_get_queue_service = deps_module.get_queue_service
    original_get_audio_service = deps_module.get_audio_service
    original_get_tts_processor = deps_module.get_tts_processor

    deps_module.get_tts_service = mock_dependencies["get_tts_service"]
    deps_module.get_voice_service = mock_dependencies["get_voice_service"]
    deps_module.get_upload_service = mock_dependencies["get_upload_service"]
    deps_module.get_queue_service = mock_dependencies["get_queue_service"]
    deps_module.get_audio_service = mock_dependencies["get_audio_service"]
    deps_module.get_tts_processor = mock_dependencies["get_tts_processor"]

    try:
        with TestClient(test_app) as client:
            yield client
    finally:
        # 恢复原始依赖注入函数
        deps_module.get_tts_service = original_get_tts_service
        deps_module.get_voice_service = original_get_voice_service
        deps_module.get_upload_service = original_get_upload_service
        deps_module.get_queue_service = original_get_queue_service
        deps_module.get_audio_service = original_get_audio_service
        deps_module.get_tts_processor = original_get_tts_processor


@pytest.fixture(scope="function")
async def test_queue():
    """创建测试队列"""
    # 队列现在通过 QueueService 管理，不需要单独的测试队列
    yield


@pytest.fixture
def sample_upload():
    """创建示例上传记录"""
    return oc8r.Upload(
        id=str(uuid.uuid4()),
        fileName="test.wav",
        contentType="audio/wav",
        sizeBytes=1024,
        durationSeconds=1.5,
        createdAt=datetime.now().isoformat(),
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
        updatedAt=datetime.now().isoformat(),
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
            text="Hello world", mode=oc8r.TtsMode.speaker, voiceId="test-voice-id"
        ),
        result=None,
        error=None,
    )


@pytest.fixture
def sample_audio_file():
    """创建示例音频文件"""
    # 创建一个简单的WAV文件头（44字节）
    wav_header = (
        b"RIFF\x24\x00\x00\x00WAVEfmt \x10\x00\x00\x00\x01\x00\x01\x00"
        b"\x44\xac\x00\x00\x88X\x01\x00\x02\x00\x10\x00data\x00\x00\x00\x00"
    )
    return wav_header


@pytest.fixture
def sample_create_voice_request():
    """创建示例音色创建请求"""
    return oc8r.CreateVoiceRequest(
        name="Test Voice",
        description="Test voice description",
        uploadId="test-upload-id",
    )


@pytest.fixture
def sample_create_tts_job_request():
    """创建示例TTS任务创建请求"""
    return oc8r.CreateTtsJobRequest(
        text="Hello world", mode=oc8r.TtsMode.speaker, voiceId="test-voice-id"
    )


@pytest.fixture
def sample_upload_file():
    """创建示例上传文件"""
    from fastapi import UploadFile
    from io import BytesIO

    # 创建模拟文件内容
    file_content = b"mock audio content"
    file_obj = BytesIO(file_content)

    # 创建UploadFile对象
    upload_file = UploadFile(filename="test.wav", file=file_obj)
    upload_file.content_type = "audio/wav"

    return upload_file


@pytest.fixture
def test_repositories(test_db):
    """创建测试仓储实例"""
    return {
        "job_repo": TtsJobRepository(test_db),
        "voice_repo": VoiceRepository(test_db),
        "upload_repo": UploadRepository(test_db),
    }


@pytest.fixture
def test_infra_services(mock_storage, mock_indextts_client, mock_queue_manager):
    """创建测试基础设施服务"""
    return {
        "storage": mock_storage,
        "indextts_client": mock_indextts_client,
        "queue_manager": mock_queue_manager,
    }
