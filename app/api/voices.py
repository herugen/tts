"""
文件级注释：
本模块负责 Voice 相关接口（/voices），属于接口层（Interface Layer）。
- 遵循分层架构，接口层仅处理 HTTP 请求、参数校验和响应组装，具体业务逻辑委托给应用层/基础设施层。
- 严格遵循 OpenAPI 规范定义的接口，所有模型均引用自动生成的模型结构体。

接口说明：
- POST   /voices           ：创建 Voice，校验 uploadId 存在、名称去重
- GET    /voices           ：分页查询 Voice（占位实现）
- GET    /voices/{id}      ：查询单个 Voice
- DELETE /voices/{id}      ：删除 Voice

依赖说明：
- 依赖 VoiceRepository 进行数据操作
- 依赖 UploadRepository 校验 uploadId
- 依赖 oc8r.Voice/VoiceResponse/VoiceListResponse 等模型
- 依赖 get_db_conn 进行数据库连接注入
"""

from fastapi import APIRouter, HTTPException, status, Depends, Query
from fastapi.responses import JSONResponse
from app.infra.repositories import VoiceRepository, UploadRepository
from app.models import oc8r
from app.db_conn import get_db_conn
from datetime import datetime
import uuid
import sqlite3
import logging
logger = logging.getLogger(__name__)

router = APIRouter()

def check_upload_exists(upload_repo, upload_id: str):
    """
    校验 uploadId 是否存在
    """
    if not upload_repo.get(upload_id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="uploadId does not exist"
        )

def check_voice_name_unique(voice_repo, name: str):
    """
    校验 Voice 名称是否唯一
    """
    voices = voice_repo.list(limit=10000, offset=0)
    for v in voices:
        if v.name == name:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Voice name already exists"
            )

@router.post(
    "/voices",
    summary="创建 Voice",
    tags=["Voices"],
    response_model=oc8r.VoiceResponse,
    status_code=status.HTTP_201_CREATED
)
async def create_voice(
    body: oc8r.CreateVoiceRequest,
    db: sqlite3.Connection = Depends(get_db_conn)
):
    """
    创建 Voice
    - 校验 uploadId 是否存在
    - 校验名称唯一
    - 创建 Voice 并返回
    """
    voice_repo = VoiceRepository(db)
    upload_repo = UploadRepository(db)
    check_upload_exists(upload_repo, body.uploadId)
    check_voice_name_unique(voice_repo, body.name)

    now = datetime.now().isoformat()
    voice_id = str(uuid.uuid4())
    voice = oc8r.Voice(
        id=voice_id,
        name=body.name,
        description=body.description,
        uploadId=body.uploadId,
        createdAt=now,
        updatedAt=now
    )
    voice_repo.add(voice)
    resp = oc8r.VoiceResponse(
        code=201,
        message="Voice created",
        voice=voice
    )
    return JSONResponse(status_code=201, content=resp.model_dump())

@router.get(
    "/voices",
    summary="分页查询 Voice",
    tags=["Voices"],
    response_model=oc8r.VoiceListResponse
)
async def list_voices(
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: sqlite3.Connection = Depends(get_db_conn)
):
    """
    分页查询 Voice（占位实现）
    """
    voice_repo = VoiceRepository(db)
    voices = voice_repo.list(limit=limit, offset=offset)
    resp = oc8r.VoiceListResponse(
        code=200,
        message="Success",
        voices=voices
    )
    return resp

@router.get(
    "/voices/{voice_id}",
    summary="查询单个 Voice",
    tags=["Voices"],
    response_model=oc8r.VoiceResponse
)
async def get_voice(
    voice_id: str,
    db: sqlite3.Connection = Depends(get_db_conn)
):
    """
    查询单个 Voice
    """
    voice_repo = VoiceRepository(db)
    voice = voice_repo.get(voice_id)
    if not voice:
        raise HTTPException(status_code=404, detail="Voice not found")
    resp = oc8r.VoiceResponse(
        code=200,
        message="Success",
        voice=voice
    )
    return resp

@router.delete(
    "/voices/{voice_id}",
    summary="删除 Voice",
    tags=["Voices"],
    response_model=oc8r.VoiceResponse
)
async def delete_voice(
    voice_id: str,
    db: sqlite3.Connection = Depends(get_db_conn)
):
    """
    删除 Voice 及其关联的 Upload 记录和文件
    - 删除 Voice 记录
    - 删除关联的 Upload 记录
    - 删除关联的音频文件
    """
    from app.infra.storage import LocalFileStorage
    
    voice_repo = VoiceRepository(db)
    upload_repo = UploadRepository(db)
    storage = LocalFileStorage()
    
    # 获取Voice记录
    voice = voice_repo.get(voice_id)
    if not voice:
        raise HTTPException(status_code=404, detail="Voice not found")
    
    # 获取关联的Upload记录
    upload = upload_repo.get(voice.uploadId)
    
    try:
        # 1. 删除Voice记录
        voice_repo.delete(voice_id)
        
        # 2. 删除关联的Upload记录
        if upload:
            upload_repo.delete(voice.uploadId)
            
            # 3. 删除关联的音频文件
            file_deleted = storage.delete_file(voice.uploadId)
            if not file_deleted:
                logger.warning(f"Failed to delete file for upload {voice.uploadId}")
        
        resp = oc8r.VoiceResponse(
            code=200,
            message="Voice and associated files deleted successfully",
            voice=voice
        )
        return resp
        
    except Exception as e:
        logger.error(f"Error deleting voice {voice_id}: {str(e)}")
        raise HTTPException(
            status_code=500, 
            detail="Failed to delete voice and associated files"
        )

