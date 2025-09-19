"""
TTS任务业务处理器

负责处理TTS任务的业务逻辑，包括：
- TTS任务处理
- 策略选择和验证
- 结果处理

职责：
- 纯业务逻辑处理
- 不包含技术实现细节
- 协调领域对象和基础设施层
"""

import logging
from typing import Any, Dict
from app.models import oc8r
from app.application.tts_strategies import TtsStrategyFactory
from app.infra.indextts_client import IndexTtsClient, IndexTtsBusyError
from app.infra.repositories import VoiceRepository, UploadRepository
from app.infra.storage import LocalFileStorage
from app.application.file_service import FileApplicationService
import asyncio
from fastapi import HTTPException

logger = logging.getLogger(__name__)


class TtsTaskProcessor:
    """
    TTS任务业务处理器

    负责处理TTS任务的业务逻辑，包括策略选择、参数验证、结果处理等。
    作为应用层的业务处理器，只包含业务逻辑，不包含技术实现细节。
    """

    def __init__(
        self,
        voice_repo: VoiceRepository,
        upload_repo: UploadRepository,
        storage: LocalFileStorage,
        client: IndexTtsClient,
        file_service: FileApplicationService,
    ):
        """
        初始化TTS任务处理器

        Args:
            voice_repo: 音色仓储
            upload_repo: 上传文件仓储
            storage: 文件存储服务
            client: IndexTTS客户端
            file_service: 文件处理服务
        """
        self.voice_repo = voice_repo
        self.upload_repo = upload_repo
        self.storage = storage
        self.client = client
        self.file_service = file_service

    async def process_tts_task(self, payload: Any) -> Dict[str, Any]:
        """
        处理TTS任务 - 纯业务逻辑，包含busy重试机制

        Args:
            payload: 任务载荷，包含请求数据

        Returns:
            Dict[str, Any]: 处理结果

        Raises:
            Exception: 当处理失败时
        """
        try:
            # 1. 解析请求数据 - 业务逻辑
            request_data = payload.get("request", {})
            request = oc8r.CreateTtsJobRequest(**request_data)

            # 2. 根据模式创建策略 - 业务逻辑
            strategy = TtsStrategyFactory.create_strategy(
                request.mode,
                self.client,
                self.voice_repo,
                self.upload_repo,
                self.storage,
                self.file_service,
            )

            # 3. 验证请求参数 - 业务逻辑
            await strategy.validate_request(request)

            # 4. 执行TTS合成 - 业务逻辑
            result = await self._synthesize_with_retry(strategy, request)

            return result

        except HTTPException as e:
            logger.error("TTS server error: %s", str(e))
            raise
        except Exception as e:
            logger.error("TTS task processing failed: %s", str(e))
            raise

    async def _synthesize_with_retry(
        self, strategy, request: oc8r.CreateTtsJobRequest
    ) -> Dict[str, Any]:
        """
        执行TTS合成，支持busy重试

        Args:
            strategy: TTS策略
            request: TTS请求

        Returns:
            Dict[str, Any]: 合成结果
        """
        max_retries = 10
        retry_count = 0

        while retry_count < max_retries:
            try:
                result = await strategy.synthesize(request)
                return result
            except IndexTtsBusyError as e:
                retry_count += 1
                if retry_count >= max_retries:
                    logger.error(
                        "IndexTTS service busy after %d retries in synthesis",
                        max_retries,
                    )
                    raise e

                logger.warning(
                    "IndexTTS service is busy, will retry in 60 seconds (%d/%d)",
                    retry_count,
                    max_retries,
                )
                await asyncio.sleep(60)
                continue
            except Exception as e:
                raise e
        raise RuntimeError("Unexpected end of retry loop")
