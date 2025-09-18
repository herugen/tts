"""
Upload应用服务

处理文件上传相关的业务协调，包括：
- 上传音频文件

职责：
- 协调领域对象和基础设施层
- 处理文件上传相关的用例
- 不包含具体的业务逻辑
"""

from datetime import datetime
from fastapi import UploadFile
from app.models.oc8r import Upload
from app.infra.storage import LocalFileStorage
from app.infra.repositories import UploadRepository


class UploadApplicationService:
    """
    Upload应用服务

    负责协调文件上传相关的业务用例，包括音频文件上传等操作。
    作为接口层和领域层之间的桥梁，只做业务协调，不包含具体业务逻辑。
    """

    def __init__(self, storage: LocalFileStorage, upload_repo: UploadRepository = None):
        """
        初始化Upload应用服务

        Args:
            storage: 本地文件存储
            upload_repo: 上传文件仓储（可选）
        """
        self.storage = storage
        self.upload_repo = upload_repo

    async def upload_file(self, file: UploadFile) -> Upload:
        """
        上传音频文件

        Args:
            file: 上传的文件对象

        Returns:
            Upload: 上传结果对象
        """

        # 使用原始文件名
        filename = file.filename

        # 保存文件
        file_id, file_path, content_type, size = self.storage.save_upload(file)

        # 创建上传记录
        upload = Upload(
            id=file_id,
            fileName=filename,
            contentType=content_type,
            sizeBytes=size,
            durationSeconds=None,
            createdAt=datetime.now().isoformat(),
        )

        # 保存到数据库（如果有仓储）
        if self.upload_repo:
            self.upload_repo.add(upload)

        return upload
