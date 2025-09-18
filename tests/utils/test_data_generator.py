"""
测试数据生成器
用于生成测试用的数据

重构后的架构说明：
- 支持应用服务层的测试数据生成
- 支持策略模式的测试数据生成
- 支持仓储层的测试数据生成
- 保持与重构后业务代码的兼容性

架构层次：
- 应用层：TtsApplicationService, VoiceApplicationService, UploadApplicationService等
- 领域层：TtsJob, Voice, Upload等模型
- 基础设施层：Repository, Storage等
- 策略层：TtsStrategy及其实现类
"""

import uuid
from datetime import datetime
from typing import Dict, Any, List
from unittest.mock import Mock
from app.models import oc8r
from app.application.tts_service import TtsApplicationService
from app.application.voice_service import VoiceApplicationService
from app.application.upload_service import UploadApplicationService
from app.application.queue_service import QueueApplicationService
from app.application.audio_service import AudioApplicationService
from app.application.file_service import FileApplicationService
from app.application.tts_processor import TtsTaskProcessor
from app.application.tts_strategies import (
    SpeakerStrategy,
    ReferenceStrategy,
    VectorStrategy,
    TextStrategy,
)
from app.infra.repositories import TtsJobRepository, VoiceRepository, UploadRepository
from app.infra.storage import LocalFileStorage
from app.infra.queue import QueueManager
from app.infra.indextts_client import IndexTtsClient


class TestDataGenerator:
    """测试数据生成器类"""

    @staticmethod
    def create_upload(
        filename: str = "test.wav",
        content_type: str = "audio/wav",
        size_bytes: int = 1024,
        duration_seconds: float = 1.5,
    ) -> oc8r.Upload:
        """创建测试上传记录"""
        return oc8r.Upload(
            id=str(uuid.uuid4()),
            fileName=filename,
            contentType=content_type,
            sizeBytes=size_bytes,
            durationSeconds=duration_seconds,
            createdAt=datetime.now().isoformat(),
        )

    @staticmethod
    def create_voice(
        name: str = "Test Voice",
        description: str = "Test voice description",
        upload_id: str = None,
    ) -> oc8r.Voice:
        """创建测试音色记录"""
        if upload_id is None:
            upload_id = str(uuid.uuid4())

        return oc8r.Voice(
            id=str(uuid.uuid4()),
            name=name,
            description=description,
            uploadId=upload_id,
            createdAt=datetime.now().isoformat(),
            updatedAt=datetime.now().isoformat(),
        )

    @staticmethod
    def create_tts_job(
        text: str = "Hello world",
        mode: oc8r.TtsMode = oc8r.TtsMode.speaker,
        voice_id: str = None,
        status: oc8r.JobStatus = oc8r.JobStatus.queued,
    ) -> oc8r.TtsJob:
        """创建测试TTS任务"""
        if voice_id is None:
            voice_id = str(uuid.uuid4())

        return oc8r.TtsJob(
            id=str(uuid.uuid4()),
            type=oc8r.Type.tts,
            status=status,
            createdAt=datetime.now().isoformat(),
            updatedAt=datetime.now().isoformat(),
            request=oc8r.CreateTtsJobRequest(text=text, mode=mode, voiceId=voice_id),
            result=None,
            error=None,
        )

    @staticmethod
    def create_speaker_mode_request(
        text: str = "Hello world", voice_id: str = None
    ) -> oc8r.CreateTtsJobRequest:
        """创建speaker模式请求"""
        if voice_id is None:
            voice_id = str(uuid.uuid4())

        return oc8r.CreateTtsJobRequest(
            text=text, mode=oc8r.TtsMode.speaker, voiceId=voice_id
        )

    @staticmethod
    def create_reference_mode_request(
        text: str = "Hello world",
        voice_id: str = None,
        emotion_audio_id: str = None,
        emotion_weight: float = 0.8,
    ) -> oc8r.CreateTtsJobRequest:
        """创建reference模式请求"""
        if voice_id is None:
            voice_id = str(uuid.uuid4())
        if emotion_audio_id is None:
            emotion_audio_id = str(uuid.uuid4())

        return oc8r.CreateTtsJobRequest(
            text=text,
            mode=oc8r.TtsMode.reference,
            voiceId=voice_id,
            emotionAudioId=emotion_audio_id,
            emotionWeight=emotion_weight,
        )

    @staticmethod
    def create_vector_mode_request(
        text: str = "Hello world",
        voice_id: str = None,
        emotion_factors: oc8r.EmotionFactors = None,
    ) -> oc8r.CreateTtsJobRequest:
        """创建vector模式请求"""
        if voice_id is None:
            voice_id = str(uuid.uuid4())
        if emotion_factors is None:
            emotion_factors = oc8r.EmotionFactors(
                happy=0.8,
                angry=0.1,
                sad=0.0,
                afraid=0.0,
                disgusted=0.0,
                melancholic=0.0,
                surprised=0.1,
                calm=0.0,
            )

        return oc8r.CreateTtsJobRequest(
            text=text,
            mode=oc8r.TtsMode.vector,
            voiceId=voice_id,
            emotionFactors=emotion_factors,
        )

    @staticmethod
    def create_text_mode_request(
        text: str = "Hello world",
        voice_id: str = None,
        emotion_text: str = "happy and excited",
    ) -> oc8r.CreateTtsJobRequest:
        """创建text模式请求"""
        if voice_id is None:
            voice_id = str(uuid.uuid4())

        return oc8r.CreateTtsJobRequest(
            text=text,
            mode=oc8r.TtsMode.text,
            voiceId=voice_id,
            emotionText=emotion_text,
        )

    @staticmethod
    def create_generation_args(
        do_sample: bool = True,
        top_p: float = 0.8,
        top_k: int = 30,
        temperature: float = 0.8,
    ) -> oc8r.GenerationArgs:
        """创建生成参数"""
        return oc8r.GenerationArgs(
            doSample=do_sample, topP=top_p, topK=top_k, temperature=temperature
        )

    @staticmethod
    def create_emotion_factors(
        happy: float = 0.8,
        angry: float = 0.1,
        sad: float = 0.0,
        afraid: float = 0.0,
        disgusted: float = 0.0,
        melancholic: float = 0.0,
        surprised: float = 0.1,
        calm: float = 0.0,
    ) -> oc8r.EmotionFactors:
        """创建情感因子"""
        return oc8r.EmotionFactors(
            happy=happy,
            angry=angry,
            sad=sad,
            afraid=afraid,
            disgusted=disgusted,
            melancholic=melancholic,
            surprised=surprised,
            calm=calm,
        )

    # ==================== 应用服务层测试数据生成 ====================

    @staticmethod
    def create_mock_repositories() -> Dict[str, Any]:
        """创建模拟的仓储对象"""
        return {
            "tts_job_repo": Mock(spec=TtsJobRepository),
            "voice_repo": Mock(spec=VoiceRepository),
            "upload_repo": Mock(spec=UploadRepository),
        }

    @staticmethod
    def create_mock_infrastructure() -> Dict[str, Any]:
        """创建模拟的基础设施对象"""
        return {
            "storage": Mock(spec=LocalFileStorage),
            "queue_manager": Mock(spec=QueueManager),
            "indextts_client": Mock(spec=IndexTtsClient),
        }

    @staticmethod
    def create_tts_application_service(
        job_repo: TtsJobRepository = None,
        voice_repo: VoiceRepository = None,
        queue_manager: QueueManager = None,
    ) -> TtsApplicationService:
        """创建TTS应用服务实例"""
        if job_repo is None:
            job_repo = Mock(spec=TtsJobRepository)
        if voice_repo is None:
            voice_repo = Mock(spec=VoiceRepository)
        if queue_manager is None:
            queue_manager = Mock(spec=QueueManager)

        return TtsApplicationService(job_repo, voice_repo, queue_manager)

    @staticmethod
    def create_voice_application_service(
        voice_repo: VoiceRepository = None,
        storage: LocalFileStorage = None,
        upload_repo: UploadRepository = None,
    ) -> VoiceApplicationService:
        """创建Voice应用服务实例"""
        if voice_repo is None:
            voice_repo = Mock(spec=VoiceRepository)
        if storage is None:
            storage = Mock(spec=LocalFileStorage)
        if upload_repo is None:
            upload_repo = Mock(spec=UploadRepository)

        return VoiceApplicationService(voice_repo, storage, upload_repo)

    @staticmethod
    def create_upload_application_service(
        storage: LocalFileStorage = None,
    ) -> UploadApplicationService:
        """创建Upload应用服务实例"""
        if storage is None:
            storage = Mock(spec=LocalFileStorage)

        return UploadApplicationService(storage)

    @staticmethod
    def create_queue_application_service(
        queue_manager: QueueManager = None,
    ) -> QueueApplicationService:
        """创建Queue应用服务实例"""
        if queue_manager is None:
            queue_manager = Mock(spec=QueueManager)

        return QueueApplicationService(queue_manager)

    @staticmethod
    def create_audio_application_service(
        storage: LocalFileStorage = None,
    ) -> AudioApplicationService:
        """创建Audio应用服务实例"""
        if storage is None:
            storage = Mock(spec=LocalFileStorage)

        return AudioApplicationService(storage)

    @staticmethod
    def create_file_application_service(
        storage: LocalFileStorage = None,
    ) -> FileApplicationService:
        """创建File应用服务实例"""
        if storage is None:
            storage = Mock(spec=LocalFileStorage)

        return FileApplicationService(storage)

    @staticmethod
    def create_tts_task_processor(
        voice_repo: VoiceRepository = None,
        upload_repo: UploadRepository = None,
        storage: LocalFileStorage = None,
        client: IndexTtsClient = None,
        file_service: FileApplicationService = None,
    ) -> TtsTaskProcessor:
        """创建TTS任务处理器实例"""
        if voice_repo is None:
            voice_repo = Mock(spec=VoiceRepository)
        if upload_repo is None:
            upload_repo = Mock(spec=UploadRepository)
        if storage is None:
            storage = Mock(spec=LocalFileStorage)
        if client is None:
            client = Mock(spec=IndexTtsClient)
        if file_service is None:
            file_service = Mock(spec=FileApplicationService)

        return TtsTaskProcessor(voice_repo, upload_repo, storage, client, file_service)

    # ==================== 策略模式测试数据生成 ====================

    @staticmethod
    def create_speaker_strategy(
        client: IndexTtsClient = None,
        voice_repo: VoiceRepository = None,
        upload_repo: UploadRepository = None,
        storage: LocalFileStorage = None,
        file_service: FileApplicationService = None,
    ) -> SpeakerStrategy:
        """创建Speaker策略实例"""
        if client is None:
            client = Mock(spec=IndexTtsClient)
        if voice_repo is None:
            voice_repo = Mock(spec=VoiceRepository)
        if upload_repo is None:
            upload_repo = Mock(spec=UploadRepository)
        if storage is None:
            storage = Mock(spec=LocalFileStorage)
        if file_service is None:
            file_service = Mock(spec=FileApplicationService)

        return SpeakerStrategy(client, voice_repo, upload_repo, storage, file_service)

    @staticmethod
    def create_reference_strategy(
        client: IndexTtsClient = None,
        voice_repo: VoiceRepository = None,
        upload_repo: UploadRepository = None,
        storage: LocalFileStorage = None,
        file_service: FileApplicationService = None,
    ) -> ReferenceStrategy:
        """创建Reference策略实例"""
        if client is None:
            client = Mock(spec=IndexTtsClient)
        if voice_repo is None:
            voice_repo = Mock(spec=VoiceRepository)
        if upload_repo is None:
            upload_repo = Mock(spec=UploadRepository)
        if storage is None:
            storage = Mock(spec=LocalFileStorage)
        if file_service is None:
            file_service = Mock(spec=FileApplicationService)

        return ReferenceStrategy(client, voice_repo, upload_repo, storage, file_service)

    @staticmethod
    def create_vector_strategy(
        client: IndexTtsClient = None,
        voice_repo: VoiceRepository = None,
        upload_repo: UploadRepository = None,
        storage: LocalFileStorage = None,
        file_service: FileApplicationService = None,
    ) -> VectorStrategy:
        """创建Vector策略实例"""
        if client is None:
            client = Mock(spec=IndexTtsClient)
        if voice_repo is None:
            voice_repo = Mock(spec=VoiceRepository)
        if upload_repo is None:
            upload_repo = Mock(spec=UploadRepository)
        if storage is None:
            storage = Mock(spec=LocalFileStorage)
        if file_service is None:
            file_service = Mock(spec=FileApplicationService)

        return VectorStrategy(client, voice_repo, upload_repo, storage, file_service)

    @staticmethod
    def create_text_strategy(
        client: IndexTtsClient = None,
        voice_repo: VoiceRepository = None,
        upload_repo: UploadRepository = None,
        storage: LocalFileStorage = None,
        file_service: FileApplicationService = None,
    ) -> TextStrategy:
        """创建Text策略实例"""
        if client is None:
            client = Mock(spec=IndexTtsClient)
        if voice_repo is None:
            voice_repo = Mock(spec=VoiceRepository)
        if upload_repo is None:
            upload_repo = Mock(spec=UploadRepository)
        if storage is None:
            storage = Mock(spec=LocalFileStorage)
        if file_service is None:
            file_service = Mock(spec=FileApplicationService)

        return TextStrategy(client, voice_repo, upload_repo, storage, file_service)

    # ==================== 模拟数据设置方法 ====================

    @staticmethod
    def setup_mock_voice_repo(voice_repo: Mock, voices: List[oc8r.Voice] = None):
        """设置模拟Voice仓储的行为"""
        if voices is None:
            voices = [TestDataGenerator.create_voice()]

        voice_repo.get.return_value = voices[0] if voices else None
        voice_repo.list.return_value = voices
        voice_repo.add.return_value = None
        voice_repo.delete.return_value = None

    @staticmethod
    def setup_mock_upload_repo(upload_repo: Mock, uploads: List[oc8r.Upload] = None):
        """设置模拟Upload仓储的行为"""
        if uploads is None:
            uploads = [TestDataGenerator.create_upload()]

        upload_repo.get.return_value = uploads[0] if uploads else None
        upload_repo.list.return_value = uploads
        upload_repo.add.return_value = None
        upload_repo.delete.return_value = None

    @staticmethod
    def setup_mock_tts_job_repo(job_repo: Mock, jobs: List[oc8r.TtsJob] = None):
        """设置模拟TtsJob仓储的行为"""
        if jobs is None:
            jobs = [TestDataGenerator.create_tts_job()]

        job_repo.get.return_value = jobs[0] if jobs else None
        job_repo.list.return_value = jobs
        job_repo.add.return_value = None
        job_repo.update.return_value = None
        job_repo.delete.return_value = None

    @staticmethod
    def setup_mock_storage(
        storage: Mock, file_exists: bool = True, file_path: str = None
    ):
        """设置模拟存储服务的行为"""
        if file_path is None:
            file_path = "/test/path/audio.wav"

        storage.get_file_path.return_value = file_path if file_exists else None
        storage.save_upload.return_value = (
            str(uuid.uuid4()),
            file_path,
            "audio/wav",
            1024,
        )
        storage.delete_file.return_value = None

    @staticmethod
    def setup_mock_queue_manager(queue_manager: Mock, job_id: str = None):
        """设置模拟队列管理器的行为"""
        if job_id is None:
            job_id = str(uuid.uuid4())

        queue_manager.enqueue.return_value = job_id
        queue_manager.cancel.return_value = None
        queue_manager.running_job_id.return_value = None
        queue_manager.queue_length.return_value = 0

    @staticmethod
    def setup_mock_indextts_client(client: Mock, audio_data: bytes = None):
        """设置模拟IndexTTS客户端的行为"""
        if audio_data is None:
            audio_data = b"mock_audio_data"

        client.synthesize_speaker.return_value = audio_data
        client.synthesize_reference.return_value = audio_data
        client.synthesize_vector.return_value = audio_data
        client.synthesize_text.return_value = audio_data

    @staticmethod
    def setup_mock_file_service(file_service: Mock, result: Dict[str, Any] = None):
        """设置模拟文件服务的行为"""
        if result is None:
            result = {
                "audioUrl": "/api/v1/audio/test.wav",
                "durationSeconds": 1.5,
                "format": "wav",
            }

        file_service.save_audio_result.return_value = result
        file_service.get_audio_file_path.return_value = "/test/path/audio.wav"
        file_service.delete_audio_file.return_value = True

    # ==================== 集成测试数据生成 ====================

    @staticmethod
    def create_complete_test_environment() -> Dict[str, Any]:
        """创建完整的测试环境，包含所有必要的模拟对象"""
        # 创建基础数据
        voice = TestDataGenerator.create_voice()
        upload = TestDataGenerator.create_upload()
        job = TestDataGenerator.create_tts_job(voice_id=voice.id)

        # 创建模拟对象
        voice_repo = Mock(spec=VoiceRepository)
        upload_repo = Mock(spec=UploadRepository)
        job_repo = Mock(spec=TtsJobRepository)
        storage = Mock(spec=LocalFileStorage)
        queue_manager = Mock(spec=QueueManager)
        client = Mock(spec=IndexTtsClient)
        file_service = Mock(spec=FileApplicationService)

        # 设置模拟行为
        TestDataGenerator.setup_mock_voice_repo(voice_repo, [voice])
        TestDataGenerator.setup_mock_upload_repo(upload_repo, [upload])
        TestDataGenerator.setup_mock_tts_job_repo(job_repo, [job])
        TestDataGenerator.setup_mock_storage(storage)
        TestDataGenerator.setup_mock_queue_manager(queue_manager, job.id)
        TestDataGenerator.setup_mock_indextts_client(client)
        TestDataGenerator.setup_mock_file_service(file_service)

        # 创建应用服务
        tts_service = TestDataGenerator.create_tts_application_service(
            job_repo, voice_repo, queue_manager
        )
        voice_service = TestDataGenerator.create_voice_application_service(
            voice_repo, storage, upload_repo
        )
        upload_service = TestDataGenerator.create_upload_application_service(storage)
        queue_service = TestDataGenerator.create_queue_application_service(
            queue_manager
        )
        audio_service = TestDataGenerator.create_audio_application_service(storage)
        file_app_service = TestDataGenerator.create_file_application_service(storage)

        # 创建任务处理器
        processor = TestDataGenerator.create_tts_task_processor(
            voice_repo, upload_repo, storage, client, file_app_service
        )

        return {
            "data": {"voice": voice, "upload": upload, "job": job},
            "repositories": {
                "voice_repo": voice_repo,
                "upload_repo": upload_repo,
                "job_repo": job_repo,
            },
            "infrastructure": {
                "storage": storage,
                "queue_manager": queue_manager,
                "client": client,
                "file_service": file_service,
            },
            "application_services": {
                "tts_service": tts_service,
                "voice_service": voice_service,
                "upload_service": upload_service,
                "queue_service": queue_service,
                "audio_service": audio_service,
                "file_service": file_app_service,
            },
            "processor": processor,
        }
