"""
文件级注释：
本模块实现本地文件存储基础设施，负责处理上传文件的校验、保存及元数据生成。遵循分层架构原则，基础设施层仅提供存储能力，不涉及业务逻辑。

架构说明：
- LocalFileStorage 类负责本地文件存储，支持音频文件（wav、mp3、m4a）。
- 所有上传文件统一存储于 data/uploads 目录，文件名采用 uuid4 生成，确保唯一性。
- 提供 save_upload 方法，校验文件类型与大小，超限返回 413 状态码。

依赖说明：
- 依赖 FastAPI 的 UploadFile 类型。
- 依赖 uuid4 生成唯一文件名。
- 依赖 os、shutil 进行文件操作。
"""

import os
import uuid
import logging
from fastapi import UploadFile, HTTPException
from typing import Tuple, Optional
from app.config import (
    UPLOAD_DIR,
    MAX_UPLOAD_BYTES,
    ALLOWED_EXTENSIONS,
    ALLOWED_MIME_TYPES,
)

logger = logging.getLogger(__name__)


class LocalFileStorage:
    """
    本地文件存储类
    负责校验并保存上传的音频文件，生成唯一文件ID和落盘路径。
    """

    def __init__(self, upload_dir: str = UPLOAD_DIR):
        """
        初始化存储目录，若不存在则自动创建。
        """
        self.upload_dir = upload_dir
        os.makedirs(self.upload_dir, exist_ok=True)

    def save_upload(self, file: UploadFile) -> Tuple[str, str, str, int]:
        """
        保存上传文件到本地磁盘，返回 (id, file_path, content_type, size_bytes)。
        校验扩展名/MIME 类型，仅允许 wav/mp3/m4a，大小不超过 20MB。
        超限抛出 HTTP 413 异常。

        :param file: FastAPI UploadFile 对象
        :return: (文件ID, 文件路径, Content-Type, 文件字节数)
        """
        # 校验扩展名
        if file.filename is None:
            raise HTTPException(status_code=400, detail="Missing filename")
        ext = self._get_extension(file.filename)
        if not self._is_allowed_extension(ext):
            raise HTTPException(status_code=415, detail="Unsupported file extension")

        # 校验 MIME 类型
        if file.content_type is None:
            raise HTTPException(status_code=400, detail="Missing content type")
        if not self._is_allowed_mime(file.content_type):
            raise HTTPException(status_code=415, detail="Unsupported content type")

        # 生成唯一文件ID
        file_id = str(uuid.uuid4())
        file_name = f"{file_id}.{ext}"
        file_path = os.path.join(self.upload_dir, file_name)

        # 读取并写入文件，同时校验大小
        size_bytes = 0
        with open(file_path, "wb") as out_file:
            while True:
                chunk = file.file.read(1024 * 1024)  # 1MB
                if not chunk:
                    break
                size_bytes += len(chunk)
                if size_bytes > MAX_UPLOAD_BYTES:
                    out_file.close()
                    os.remove(file_path)
                    raise HTTPException(
                        status_code=413, detail="File too large (max 20MB)"
                    )
                out_file.write(chunk)

        return (
            file_id,
            file_path,
            file.content_type or "application/octet-stream",
            size_bytes,
        )

    def _get_extension(self, filename: str) -> str:
        """
        获取文件扩展名（小写，无点号）。
        """
        return os.path.splitext(filename)[-1].lower().lstrip(".")

    def _is_allowed_extension(self, ext: str) -> bool:
        """
        判断扩展名是否允许。
        """
        return ext in ALLOWED_EXTENSIONS

    def _is_allowed_mime(self, mime: str) -> bool:
        """
        判断 MIME 类型是否允许。
        """
        return mime in ALLOWED_MIME_TYPES

    def delete_file(self, file_id: str) -> bool:
        """
        删除指定ID的文件
        :param file_id: 文件ID
        :return: 是否删除成功
        """
        try:
            # 查找文件（通过文件ID匹配文件名）
            for filename in os.listdir(self.upload_dir):
                if filename.startswith(file_id):
                    file_path = os.path.join(self.upload_dir, filename)
                    if os.path.exists(file_path):
                        os.remove(file_path)
                        return True
            return False
        except OSError as e:
            logger.error("Failed to delete file %s: %s", file_id, str(e))
            return False

    def get_file_path(self, file_id: str) -> Optional[str]:
        """
        根据文件ID获取文件路径
        :param file_id: 文件ID
        :return: 文件路径，如果不存在返回None
        """
        try:
            for filename in os.listdir(self.upload_dir):
                if filename.startswith(file_id):
                    file_path = os.path.join(self.upload_dir, filename)
                    if os.path.exists(file_path):
                        return file_path
            return None
        except OSError as e:
            logger.error("Failed to get file path for %s: %s", file_id, str(e))
            return None

    async def save_audio_file(self, audio_data: bytes, filename: str) -> str:
        """
        保存音频文件到输出目录
        :param audio_data: 音频数据
        :param filename: 文件名
        :return: 文件路径
        """
        try:
            # 确保输出目录存在
            output_dir = "data/outputs"
            os.makedirs(output_dir, exist_ok=True)

            # 构建完整文件路径
            file_path = os.path.join(output_dir, filename)

            # 写入文件
            with open(file_path, "wb") as f:
                f.write(audio_data)

            return file_path
        except OSError as e:
            logger.error("Failed to save audio file %s: %s", filename, str(e))
            raise

    async def get_audio_file_path(self, filename: str) -> Optional[str]:
        """
        获取音频文件路径
        :param filename: 文件名
        :return: 文件路径，如果不存在返回None
        """
        try:
            output_dir = "data/outputs"
            file_path = os.path.join(output_dir, filename)

            if os.path.exists(file_path):
                return file_path
            return None
        except OSError as e:
            logger.error("Failed to get audio file path for %s: %s", filename, str(e))
            return None

    async def delete_audio_file(self, filename: str) -> bool:
        """
        删除音频文件
        :param filename: 文件名
        :return: 是否删除成功
        """
        try:
            output_dir = "data/outputs"
            file_path = os.path.join(output_dir, filename)

            if os.path.exists(file_path):
                os.remove(file_path)
                return True
            return False
        except OSError as e:
            logger.error("Failed to delete audio file %s: %s", filename, str(e))
            return False
