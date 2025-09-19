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
from app.models import oc8r
from app.dependencies import get_voice_service
from app.application.voice_service import VoiceService

router = APIRouter()


@router.post(
    "/voices",
    summary="创建 Voice",
    tags=["Voices"],
    response_model=oc8r.VoiceResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_voice(
    body: oc8r.CreateVoiceRequest,
    voice_service: VoiceService = Depends(get_voice_service),
):
    """
    创建 Voice
    - 委托给Voice应用服务处理业务逻辑
    """
    try:
        # 委托给Voice应用服务创建音色
        voice = await voice_service.create_voice(body)

        # 构建响应
        resp = oc8r.VoiceResponse(code=201, message="Voice created", voice=voice)
        return JSONResponse(status_code=201, content=resp.model_dump())

    except ValueError as e:
        # 业务逻辑错误，如音色名称重复或uploadId不存在
        raise HTTPException(status_code=400, detail=str(e)) from e
    except Exception:
        # 其他系统错误
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get(
    "/voices",
    summary="分页查询 Voice",
    tags=["Voices"],
    response_model=oc8r.VoiceListResponse,
)
async def list_voices(
    limit: int = Query(100, ge=0),
    offset: int = Query(0, ge=0),
    voice_service: VoiceService = Depends(get_voice_service),
):
    """
    分页查询 Voice
    - 委托给Voice应用服务处理业务逻辑
    """
    # 委托给Voice应用服务获取音色列表
    voices = await voice_service.list_voices(offset=offset, limit=limit)

    resp = oc8r.VoiceListResponse(code=200, message="Success", voices=voices)
    return resp


@router.get(
    "/voices/{voice_id}",
    summary="查询单个 Voice",
    tags=["Voices"],
    response_model=oc8r.VoiceResponse,
)
async def get_voice(
    voice_id: str, voice_service: VoiceService = Depends(get_voice_service)
):
    """
    查询单个 Voice
    - 委托给Voice应用服务处理业务逻辑
    """
    # 委托给Voice应用服务获取音色
    voice = await voice_service.get_voice(voice_id)
    if not voice:
        raise HTTPException(status_code=404, detail="Voice not found")

    resp = oc8r.VoiceResponse(code=200, message="Success", voice=voice)
    return resp


@router.delete(
    "/voices/{voice_id}",
    summary="删除 Voice",
    tags=["Voices"],
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_voice(
    voice_id: str, voice_service: VoiceService = Depends(get_voice_service)
):
    """
    删除 Voice 及其关联的 Upload 记录和文件
    - 委托给Voice应用服务处理业务逻辑
    """
    try:
        # 委托给Voice应用服务删除音色
        success = await voice_service.delete_voice(voice_id)
        if not success:
            raise HTTPException(status_code=404, detail="Voice not found")

        # 删除成功，返回204状态码（无响应体）
        return None

    except HTTPException as e:
        raise e
    except ValueError as e:
        # 业务逻辑错误
        raise HTTPException(status_code=400, detail=str(e)) from e
    except Exception:
        # 其他系统错误
        raise HTTPException(status_code=500, detail="Internal server error")
