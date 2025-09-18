"""
文件级注释：
本模块负责实现 /uploads 文件上传接口，属于接口层（Interface Layer）。
遵循分层架构原则，接口层仅处理 HTTP 请求、参数校验和响应组装，具体存储逻辑委托给基础设施层 LocalFileStorage。

接口说明：
- 路由: POST /uploads
- 请求: multipart/form-data，字段名为 file
- 响应: UploadResponse（见 app/models/oc8r.py），upload 字段包含上传文件元信息
- 目前不做音频时长分析，durationSeconds 字段返回 None

依赖说明：
- 依赖 LocalFileStorage 进行文件校验与保存
- 依赖 oc8r.UploadResponse/Upload 组装响应体
"""

from fastapi import APIRouter, UploadFile, File, status, Depends
from fastapi.responses import JSONResponse
from app.infra.storage import LocalFileStorage
from app.models import oc8r
from datetime import datetime
from app.infra.repositories import UploadRepository
from app.db_conn import get_db_conn
import sqlite3

router = APIRouter()

@router.post(
    "/uploads",
    summary="上传音频文件",
    tags=["Uploads"],
    response_model=oc8r.UploadResponse,
    status_code=status.HTTP_201_CREATED
)
async def upload_file(
    file: UploadFile = File(...),
    db: sqlite3.Connection = Depends(get_db_conn)
):
    """
    上传音频文件接口
    - 使用 LocalFileStorage.save_upload 校验并保存文件
    - 返回 UploadResponse，包含 upload 字段
    - durationSeconds 暂时返回 None
    - 数据库连接通过 FastAPI 依赖注入获取
    """
    storage = LocalFileStorage()
    file_id, _, content_type, size_bytes = storage.save_upload(file)

    upload = oc8r.Upload(
        id=file_id,
        fileName=file.filename,
        contentType=content_type,
        sizeBytes=size_bytes,
        durationSeconds=None,  # 目前不做时长分析
        createdAt=datetime.now().isoformat()
    )
    upload_repo = UploadRepository(db)
    upload_repo.add(upload)

    resp = oc8r.UploadResponse(
        code=201,
        message="Upload succeeded",
        upload=upload
    )
    return JSONResponse(status_code=201, content=resp.model_dump())
