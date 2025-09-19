"""
应用服务容器

负责管理所有应用服务的初始化、依赖注入和生命周期管理。
遵循依赖注入模式，统一管理应用层的服务实例。

架构说明：
- 使用容器模式管理所有应用服务
- 支持依赖注入，便于测试和扩展
- 统一管理服务实例的生命周期
- 提供清晰的服务获取接口

职责：
- 初始化所有应用服务
- 管理服务依赖关系
- 提供服务获取接口
- 支持服务替换和扩展
"""

from typing import Optional
import sqlite3
from app.infra.repositories import TtsJobRepository, VoiceRepository, UploadRepository
from app.infra.queue import get_queue_manager
from app.infra.storage import LocalFileStorage
from app.application.tts_service import TtsService
from app.application.voice_service import VoiceService
from app.application.upload_service import UploadService
from app.application.queue_service import QueueService
from app.application.audio_service import AudioService
from app.application.tts_processor import TtsTaskProcessor
from app.application.file_service import FileService
from app.infra.indextts_client import IndexTtsClient
from app.db_conn import get_db_conn


class ApplicationContainer:
    """
    应用服务容器

    负责管理所有应用服务的初始化、依赖注入和生命周期管理。
    使用单例模式，确保全局只有一个容器实例。
    """

    _instance: Optional["ApplicationContainer"] = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        """初始化应用服务容器"""
        if hasattr(self, "_initialized"):
            return

        self._initialized = True
        self._services = {}
        self._initialized_services = set()

    def get_tts_service(self, db: Optional[sqlite3.Connection] = None) -> TtsService:
        """
        获取TTS服务实例

        Args:
            db: 数据库连接，如果为None则使用默认连接

        Returns:
            TtsService: TTS服务实例
        """
        if db is None:
            db = get_db_conn()

        service_key = f"tts_service_{id(db)}"
        if service_key not in self._services:
            job_repo = TtsJobRepository(db)
            voice_repo = VoiceRepository(db)
            queue_manager = get_queue_manager()

            self._services[service_key] = TtsService(
                job_repo, voice_repo, queue_manager
            )
            self._initialized_services.add(service_key)

        return self._services[service_key]

    def get_voice_service(
        self, db: Optional[sqlite3.Connection] = None
    ) -> VoiceService:
        """
        获取Voice服务实例

        Args:
            db: 数据库连接，如果为None则使用默认连接

        Returns:
            VoiceService: Voice服务实例
        """
        if db is None:
            db = get_db_conn()

        service_key = f"voice_service_{id(db)}"
        if service_key not in self._services:
            voice_repo = VoiceRepository(db)
            upload_repo = UploadRepository(db)
            storage = LocalFileStorage()

            self._services[service_key] = VoiceService(voice_repo, storage, upload_repo)
            self._initialized_services.add(service_key)

        return self._services[service_key]

    def get_upload_service(
        self, db: Optional[sqlite3.Connection] = None
    ) -> UploadService:
        """
        获取Upload服务实例

        Args:
            db: 数据库连接，如果为None则使用默认连接

        Returns:
            UploadService: Upload服务实例
        """
        if db is None:
            db = get_db_conn()

        service_key = f"upload_service_{id(db)}"
        if service_key not in self._services:
            storage = LocalFileStorage()
            upload_repo = UploadRepository(db)

            self._services[service_key] = UploadService(storage, upload_repo)
            self._initialized_services.add(service_key)

        return self._services[service_key]

    def get_queue_service(
        self, db: Optional[sqlite3.Connection] = None
    ) -> QueueService:
        """
        获取Queue服务实例

        Args:
            db: 数据库连接，如果为None则使用默认连接

        Returns:
            QueueService: Queue服务实例
        """
        if db is None:
            db = get_db_conn()

        service_key = f"queue_service_{id(db)}"
        if service_key not in self._services:
            queue_manager = get_queue_manager()
            # 通过容器获取TTS处理器依赖
            tts_processor = self.get_tts_processor(db)

            self._services[service_key] = QueueService(queue_manager, tts_processor)
            self._initialized_services.add(service_key)

        return self._services[service_key]

    def get_audio_service(
        self, db: Optional[sqlite3.Connection] = None
    ) -> AudioService:
        """
        获取Audio服务实例

        Args:
            db: 数据库连接，如果为None则使用默认连接

        Returns:
            AudioService: Audio服务实例
        """
        if db is None:
            db = get_db_conn()

        service_key = f"audio_service_{id(db)}"
        if service_key not in self._services:
            # 音频服务依赖文件服务
            file_service = self.get_file_service(db)
            self._services[service_key] = AudioService(file_service)
            self._initialized_services.add(service_key)

        return self._services[service_key]

    def get_tts_processor(
        self, db: Optional[sqlite3.Connection] = None
    ) -> TtsTaskProcessor:
        """通过容器获取TTS处理器，统一依赖管理"""
        if db is None:
            db = get_db_conn()

        service_key = f"tts_processor_{id(db)}"
        if service_key not in self._services:
            # 通过容器获取所有依赖
            voice_repo = VoiceRepository(db)
            upload_repo = UploadRepository(db)
            storage = LocalFileStorage()
            client = IndexTtsClient()
            file_service = self.get_file_service(db)

            self._services[service_key] = TtsTaskProcessor(
                voice_repo=voice_repo,
                upload_repo=upload_repo,
                storage=storage,
                client=client,
                file_service=file_service,
            )

        return self._services[service_key]

    def get_file_service(self, db: Optional[sqlite3.Connection] = None) -> FileService:
        """
        获取文件处理服务实例

        Args:
            db: 数据库连接，如果为None则使用默认连接

        Returns:
            FileService: 文件处理服务实例
        """
        if db is None:
            db = get_db_conn()

        service_key = f"file_service_{id(db)}"
        if service_key not in self._services:
            storage = LocalFileStorage()

            self._services[service_key] = FileService(storage)
            self._initialized_services.add(service_key)

        return self._services[service_key]

    def get_all_services(self, db: Optional[sqlite3.Connection] = None) -> dict:
        """
        获取所有应用服务实例

        Args:
            db: 数据库连接，如果为None则使用默认连接

        Returns:
            dict: 包含所有应用服务的字典
        """
        return {
            "tts_service": self.get_tts_service(db),
            "voice_service": self.get_voice_service(db),
            "upload_service": self.get_upload_service(db),
            "queue_service": self.get_queue_service(db),
            "audio_service": self.get_audio_service(db),
            "tts_processor": self.get_tts_processor(),
            "file_service": self.get_file_service(db),
        }

    def clear_services(self):
        """
        清理所有服务实例（主要用于测试）
        """
        self._services.clear()
        self._initialized_services.clear()


# 全局应用服务容器实例
app_container = ApplicationContainer()
