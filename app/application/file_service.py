"""
文件处理应用服务

负责处理文件相关的业务逻辑，包括：
- 音频文件保存
- 文件路径生成
- 文件访问控制

职责：
- 纯业务逻辑处理
- 不包含技术实现细节
- 协调文件存储和业务规则
"""

import uuid
import logging
from typing import Dict, Any
from app.infra.storage import LocalFileStorage

logger = logging.getLogger(__name__)


class FileApplicationService:
    """
    文件处理应用服务

    负责处理文件相关的业务逻辑，包括音频文件保存、路径生成等。
    作为应用层的业务服务，只包含业务逻辑，不包含技术实现细节。
    """

    def __init__(self, storage: LocalFileStorage):
        """
        初始化文件处理应用服务

        Args:
            storage: 文件存储服务
        """
        self.storage = storage

    async def save_audio_result(
        self, audio_data: bytes, job_id: str = None
    ) -> Dict[str, Any]:
        """
        保存音频结果 - 业务逻辑

        Args:
            audio_data: 音频数据
            job_id: 任务ID，如果为None则生成新的UUID

        Returns:
            Dict[str, Any]: 保存结果，包含audioUrl等信息
        """
        try:
            # 生成文件名 - 业务逻辑
            if job_id:
                output_filename = f"{job_id}.wav"
            else:
                output_filename = f"{uuid.uuid4()}.wav"

            # 委托给存储服务保存文件
            file_path = await self.storage.save_audio_file(audio_data, output_filename)

            # 构建返回结果 - 业务逻辑
            result = {
                "audioUrl": f"/api/v1/audio/{output_filename}",
                "durationSeconds": None,  # 规范中没有duration字段
                "format": "wav",
            }

            logger.info("Audio file saved: %s", file_path)
            return result

        except Exception as e:
            logger.error("Failed to save audio file: %s", str(e))
            raise

    async def get_audio_file_path(self, filename: str) -> str:
        """
        获取音频文件路径 - 业务逻辑

        Args:
            filename: 文件名

        Returns:
            str: 文件路径
        """
        # 委托给存储服务获取文件路径
        file_path = await self.storage.get_audio_file_path(filename)

        if not file_path:
            raise FileNotFoundError(f"Audio file not found: {filename}")

        return file_path

    async def delete_audio_file(self, filename: str) -> bool:
        """
        删除音频文件 - 业务逻辑

        Args:
            filename: 文件名

        Returns:
            bool: 删除是否成功
        """
        try:
            # 委托给存储服务删除文件
            success = await self.storage.delete_audio_file(filename)

            if success:
                logger.info("Audio file deleted: %s", filename)
            else:
                logger.warning("Audio file not found for deletion: %s", filename)

            return success

        except OSError as e:
            logger.error("Failed to delete audio file %s: %s", filename, str(e))
            return False
