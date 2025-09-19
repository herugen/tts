"""
Audio应用服务

处理音频文件访问相关的业务协调，包括：
- 获取音频文件

职责：
- 协调领域对象和基础设施层
- 处理音频文件访问相关的用例
- 不包含具体的业务逻辑
"""

from typing import Optional
from fastapi.responses import FileResponse
from app.application.file_service import FileService


class AudioService:
    """
    Audio服务

    负责协调音频文件访问相关的业务用例，包括音频文件获取等操作。
    作为接口层和领域层之间的桥梁，只做业务协调，不包含具体业务逻辑。
    """

    def __init__(self, file_service: "FileService"):
        """
        初始化Audio服务

        Args:
            file_service: 文件处理服务
        """
        self.file_service = file_service

    async def get_audio_file(self, filename: str) -> Optional[FileResponse]:
        """
        获取音频文件

        Args:
            filename: 音频文件名

        Returns:
            FileResponse: 音频文件响应，如果文件不存在则返回None
        """
        try:
            # 委托给文件服务获取文件路径
            file_path = await self.file_service.get_audio_file_path(filename)

            # 返回文件响应
            return FileResponse(
                path=file_path, media_type="audio/wav", filename=filename
            )
        except FileNotFoundError:
            # 文件不存在，返回None
            return None
