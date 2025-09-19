"""
TTS应用服务

处理TTS任务相关的业务协调，包括：
- 创建TTS任务
- 查询TTS任务状态
- 列举TTS任务
- 取消TTS任务
- 重试TTS任务

职责：
- 协调领域对象和基础设施层
- 处理TTS任务相关的用例
- 不包含具体的业务逻辑
"""

from typing import List, Optional, Any
from datetime import datetime
from app.models.oc8r import (
    TtsJob,
    CreateTtsJobRequest,
    JobStatus,
    Type,
    Result,
    ErrorResponse,
)
from app.infra.repositories import TtsJobRepository, VoiceRepository
from app.infra.queue import QueueManager
import logging

logger = logging.getLogger(__name__)


class TtsService:
    """
    TTS服务

    负责协调TTS任务相关的业务用例，包括任务创建、查询、取消、重试等操作。
    作为接口层和领域层之间的桥梁，只做业务协调，不包含具体业务逻辑。
    """

    def __init__(
        self,
        job_repo: TtsJobRepository,
        voice_repo: VoiceRepository,
        queue_manager: QueueManager,
    ):
        """
        初始化TTS服务

        Args:
            job_repo: TTS任务仓储
            voice_repo: 音色仓储
            queue_manager: 队列管理器
        """
        self.job_repo = job_repo
        self.voice_repo = voice_repo
        self.queue_manager = queue_manager
        self.queue_manager.set_callback(self.handle_status_change)

    async def create_job(self, request: CreateTtsJobRequest) -> TtsJob:
        """
        创建TTS任务

        Args:
            request: 创建TTS任务请求

        Returns:
            TtsJob: 创建的TTS任务

        Raises:
            ValueError: 当音色不存在时
        """
        # 1. 验证音色存在
        voice = self.voice_repo.get(request.voiceId)
        if not voice:
            raise ValueError("Voice not found")

        # 2. 入队
        job_id = await self.queue_manager.enqueue(
            {"request": request.model_dump(), "createdAt": datetime.now().isoformat()}
        )

        # 3. 保存到数据库
        job = TtsJob(
            id=job_id,
            type=Type.tts,  # TTS任务默认为tts类型
            status=JobStatus.queued,
            createdAt=datetime.now().isoformat(),
            updatedAt=datetime.now().isoformat(),
            request=request,
            result=None,
            error=None,
        )
        self.job_repo.add(job)

        return job

    async def get_job(self, job_id: str) -> Optional[TtsJob]:
        """
        获取TTS任务详情

        Args:
            job_id: 任务ID

        Returns:
            TtsJob: TTS任务对象，如果不存在则返回None
        """
        return self.job_repo.get(job_id)

    async def list_jobs(
        self, status: Optional[str] = None, limit: int = 100, offset: int = 0
    ) -> List[TtsJob]:
        """
        列举TTS任务

        Args:
            status: 任务状态过滤
            limit: 每页大小
            offset: 偏移量

        Returns:
            List[TtsJob]: TTS任务列表
        """
        return self.job_repo.list(status=status, limit=limit, offset=offset)

    async def cancel_job(self, job_id: str) -> Optional[TtsJob]:
        """
        取消TTS任务

        Args:
            job_id: 任务ID

        Returns:
            TtsJob: 取消后的TTS任务对象，如果不存在则返回None
        """
        job = self.job_repo.get(job_id)
        if not job:
            return None

        if job.status not in [JobStatus.queued, JobStatus.running]:
            raise ValueError(f"Cannot cancel job with status: {job.status}")

        await self.queue_manager.cancel(job_id)
        job.status = JobStatus.cancelled
        job.updatedAt = datetime.now().isoformat()
        self.job_repo.update(
            job_id, status=JobStatus.cancelled, updatedAt=job.updatedAt
        )
        return job

    async def retry_job(self, job_id: str) -> Optional[TtsJob]:
        """
        重试TTS任务

        Args:
            job_id: 任务ID

        Returns:
            TtsJob: 重试后的TTS任务对象，如果不存在则返回None
        """
        job = self.job_repo.get(job_id)
        if not job:
            return None

        if job.status not in [JobStatus.failed, JobStatus.cancelled]:
            raise ValueError(f"Cannot retry job with status: {job.status}")

        # 创建新的任务（重试）
        if job.request is None:
            raise ValueError("Cannot retry job without request data")
        new_job_id = await self.queue_manager.enqueue(
            {
                "request": job.request.model_dump(),
                "createdAt": datetime.now().isoformat(),
            }
        )

        new_job = TtsJob(
            id=new_job_id,
            type=job.type,
            status=JobStatus.queued,
            createdAt=datetime.now().isoformat(),
            updatedAt=datetime.now().isoformat(),
            request=job.request,
            result=None,
            error=None,
        )

        # 保存新任务到数据库
        self.job_repo.add(new_job)
        return new_job

    async def handle_status_change(
        self, job_id: str, status: JobStatus, result: Optional[Any] = None
    ) -> None:
        """
        处理任务状态变更的持久化回调

        这个方法会被QueueManager的状态变更回调调用，负责将状态变更持久化到数据库。
        作为应用层的业务协调，确保数据一致性。

        Args:
            job_id: 任务ID
            status: 新的任务状态
            result: 任务结果（可选）
        """
        try:
            # 获取当前任务信息
            job = self.job_repo.get(job_id)
            if not job:
                logger.warning(
                    "Job %s not found in database, skipping status update", job_id
                )
                return

            # 准备更新数据
            update_result: Optional[Result] = None
            update_error: Optional[ErrorResponse] = None

            # 根据状态处理结果数据
            if status == JobStatus.succeeded and result:
                update_result = Result(**result)

            elif status == JobStatus.failed and result:
                update_error = ErrorResponse(code="TTS_ERROR", message=str(result))

            # 执行数据库更新
            self.job_repo.update(
                job_id,
                status=status,
                result=update_result,
                error=update_error,
                updatedAt=datetime.now().isoformat(),
            )

        except (ValueError, TypeError, KeyError) as e:
            logger.error("Failed to update job %s status to %s: %s", job_id, status, e)
