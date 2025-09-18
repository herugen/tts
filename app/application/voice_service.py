"""
Voice应用服务

处理音色管理相关的业务协调，包括：
- 创建音色
- 获取音色详情
- 列举音色
- 删除音色

职责：
- 协调领域对象和基础设施层
- 处理音色管理相关的用例
- 不包含具体的业务逻辑
"""

from typing import List, Optional
from datetime import datetime
import uuid
from app.models.oc8r import Voice, CreateVoiceRequest
from app.infra.repositories import VoiceRepository, UploadRepository
from app.infra.storage import LocalFileStorage


class VoiceApplicationService:
    """
    Voice应用服务

    负责协调音色管理相关的业务用例，包括音色创建、查询、删除等操作。
    作为接口层和领域层之间的桥梁，只做业务协调，不包含具体业务逻辑。
    """

    def __init__(
        self,
        voice_repo: VoiceRepository,
        storage: LocalFileStorage,
        upload_repo: UploadRepository = None,
    ):
        """
        初始化Voice应用服务

        Args:
            voice_repo: 音色仓储
            storage: 本地文件存储
            upload_repo: 上传文件仓储（可选）
        """
        self.voice_repo = voice_repo
        self.storage = storage
        self.upload_repo = upload_repo

    async def create_voice(self, request: CreateVoiceRequest) -> Voice:
        """
        创建音色

        Args:
            request: 创建音色请求

        Returns:
            Voice: 创建的音色对象

        Raises:
            ValueError: 当音色名称重复或uploadId不存在时
        """
        # 1. 检查音色名称是否重复
        existing_voices = self.voice_repo.list(limit=1000)  # 获取所有音色
        for voice in existing_voices:
            if voice.name == request.name:
                raise ValueError("Voice name already exists")

        # 2. 检查uploadId是否存在（如果有upload_repo）
        if self.upload_repo:
            upload = self.upload_repo.get(request.uploadId)
            if not upload:
                raise ValueError("Upload ID not found")

        voice_id = str(uuid.uuid4())
        voice = Voice(
            id=voice_id,
            name=request.name,
            description=request.description,
            uploadId=request.uploadId,
            createdAt=datetime.now().isoformat(),
            updatedAt=datetime.now().isoformat(),
        )
        self.voice_repo.add(voice)
        return voice

    async def get_voice(self, voice_id: str) -> Optional[Voice]:
        """
        获取音色详情

        Args:
            voice_id: 音色ID

        Returns:
            Voice: 音色对象，如果不存在则返回None
        """
        return self.voice_repo.get(voice_id)

    async def list_voices(self, offset: int = 0, limit: int = 100) -> List[Voice]:
        """
        列举音色

        Args:
            page: 页码
            page_size: 每页大小

        Returns:
            List[Voice]: 音色列表
        """
        return self.voice_repo.list(offset=offset, limit=limit)

    async def delete_voice(self, voice_id: str) -> bool:
        """
        删除音色

        Args:
            voice_id: 音色ID

        Returns:
            bool: 删除是否成功
        """
        voice = self.voice_repo.get(voice_id)
        if voice:
            # 删除关联的音频文件
            if voice.uploadId:
                self.storage.delete_file(voice.uploadId)
            self.voice_repo.delete(voice_id)
            return True
        return False
