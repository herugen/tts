"""
文件级注释：
本模块负责 TTS 任务相关接口（/tts/jobs），属于接口层（Interface Layer）。
- 遵循分层架构，接口层仅处理 HTTP 请求、参数校验和响应组装，具体业务逻辑委托给应用层/基础设施层。
- 严格遵循 OpenAPI 规范定义的接口，所有模型均引用自动生成的模型结构体。

接口说明：
- POST   /tts/jobs                ：提交 TTS 任务，入队并返回 202 TtsJobResponse（状态为 queued）
- GET    /tts/jobs/{id}           ：查询 TTS 任务
- GET    /tts/jobs                ：查询 TTS 任务
- POST   /tts/jobs/{id}/cancel    ：取消 TTS 任务（占位/最小实现）
- POST   /tts/jobs/{id}/retry     ：重试 TTS 任务（占位/最小实现）

依赖说明：
- 依赖 TtsJobRepository 进行数据操作（占位，后续实现）
- 依赖 oc8r.TtsJobRequest/TtsJobResponse 等模型
- 依赖 get_db_conn 进行数据库连接注入
"""

from fastapi import APIRouter, status, HTTPException, Depends
from fastapi.responses import JSONResponse
from app.models import oc8r
from app.dependencies import get_tts_service
from app.application.tts_service import TtsApplicationService

router = APIRouter()


@router.post(
    "/tts/jobs",
    summary="提交 TTS 任务（入队）",
    tags=["TTS Jobs"],
    response_model=oc8r.TtsJobResponse,
    status_code=status.HTTP_202_ACCEPTED,
)
async def create_tts_job(
    body: oc8r.CreateTtsJobRequest,
    tts_service: TtsApplicationService = Depends(get_tts_service),
):
    """
    提交 TTS 任务，入队并返回 202 TtsJobResponse（状态为 queued）
    - 委托给TTS应用服务处理业务逻辑
    """
    try:
        # 委托给TTS应用服务创建任务
        job = await tts_service.create_job(body)

        # 构建响应
        resp = oc8r.TtsJobResponse(code=202, message="Job queued", job=job)
        return JSONResponse(status_code=202, content=resp.model_dump(mode="json"))

    except ValueError as e:
        # 业务逻辑错误，如音色不存在
        raise HTTPException(status_code=400, detail=str(e)) from e
    except Exception:
        # 其他系统错误
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get(
    "/tts/jobs/{job_id}",
    summary="查询 TTS 任务（占位）",
    tags=["TTS Jobs"],
    response_model=oc8r.TtsJobResponse,
    status_code=status.HTTP_200_OK,
)
async def get_tts_job(
    job_id: str, tts_service: TtsApplicationService = Depends(get_tts_service)
):
    """
    查询 TTS 任务
    - 委托给TTS应用服务处理业务逻辑
    """
    # 委托给TTS应用服务获取任务
    job = await tts_service.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    resp = oc8r.TtsJobResponse(code=200, message="Job found", job=job)
    return JSONResponse(status_code=200, content=resp.model_dump(mode="json"))


@router.get(
    "/tts/jobs",
    summary="查询 TTS 任务",
    tags=["TTS Jobs"],
    response_model=oc8r.TtsJobListResponse,
    status_code=status.HTTP_200_OK,
)
async def list_tts_jobs(
    job_status: str = None,
    limit: int = 100,
    offset: int = 0,
    tts_service: TtsApplicationService = Depends(get_tts_service),
):
    """
    查询 TTS 任务
    - 委托给TTS应用服务处理业务逻辑
    """
    # 委托给TTS应用服务获取任务列表
    jobs = await tts_service.list_jobs(status=job_status, limit=limit, offset=offset)

    resp = oc8r.TtsJobListResponse(code=200, message="Jobs found", jobs=jobs)
    return JSONResponse(status_code=200, content=resp.model_dump(mode="json"))


@router.post(
    "/tts/jobs/{job_id}/cancel",
    summary="取消 TTS 任务",
    tags=["TTS Jobs"],
    response_model=oc8r.TtsJobResponse,
    status_code=status.HTTP_200_OK,
)
async def cancel_tts_job(
    job_id: str, tts_service: TtsApplicationService = Depends(get_tts_service)
):
    """
    取消 TTS 任务
    - 委托给TTS应用服务处理业务逻辑
    """
    try:
        # 委托给TTS应用服务取消任务
        job = await tts_service.cancel_job(job_id)
        if not job:
            raise HTTPException(status_code=404, detail="Job not found")

        resp = oc8r.TtsJobResponse(
            code=200, message="Job cancelled successfully", job=job
        )
        return JSONResponse(status_code=200, content=resp.model_dump(mode="json"))

    except HTTPException as e:
        raise e
    except ValueError as e:
        # 业务逻辑错误，如任务状态不允许取消
        raise HTTPException(status_code=400, detail=str(e)) from e
    except Exception:
        # 其他系统错误
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post(
    "/tts/jobs/{job_id}/retry",
    summary="重试 TTS 任务",
    tags=["TTS Jobs"],
    response_model=oc8r.TtsJobResponse,
    status_code=status.HTTP_201_CREATED,
)
async def retry_tts_job(
    job_id: str, tts_service: TtsApplicationService = Depends(get_tts_service)
):
    """
    重试 TTS 任务
    - 委托给TTS应用服务处理业务逻辑
    """
    try:
        # 委托给TTS应用服务重试任务
        job = await tts_service.retry_job(job_id)
        if not job:
            raise HTTPException(status_code=404, detail="Job not found")

        resp = oc8r.TtsJobResponse(
            code=201, message="Job retry created successfully", job=job
        )
        return JSONResponse(status_code=201, content=resp.model_dump(mode="json"))

    except HTTPException as e:
        raise e
    except ValueError as e:
        # 业务逻辑错误，如任务状态不允许重试
        raise HTTPException(status_code=400, detail=str(e)) from e
    except Exception:
        # 其他系统错误
        raise HTTPException(status_code=500, detail="Internal server error")
