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

from fastapi import APIRouter, UploadFile, File, status, Depends, HTTPException
from fastapi.responses import JSONResponse
from app.models import oc8r
from app.dependencies import get_upload_service
from app.application.upload_service import UploadApplicationService

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
    upload_service: UploadApplicationService = Depends(get_upload_service)
):
    """
    上传音频文件接口
    - 委托给Upload应用服务处理业务逻辑
    """
    try:
        if not file.content_type or not file.content_type.startswith('audio/'):
            raise HTTPException(status_code=415, detail="Only audio files are supported")
        
        if file.size > 20 * 1024 * 1024:
            raise HTTPException(status_code=413, detail="File too large")
        
        # 委托给Upload应用服务上传文件
        upload = await upload_service.upload_file(file)
        
        # 构建响应
        resp = oc8r.UploadResponse(
            code=201,
            message="Upload succeeded",
            upload=upload
        )
        return JSONResponse(status_code=201, content=resp.model_dump())
        
    except HTTPException as e:
        raise e
    except ValueError as e:
        # 业务逻辑错误，如文件类型不支持
        raise HTTPException(status_code=400, detail=str(e)) from e
    except Exception:
        # 其他系统错误
        raise HTTPException(status_code=500, detail="Internal server error")
