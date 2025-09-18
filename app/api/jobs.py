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
from datetime import datetime
import uuid
# from typing import Optional  # 暂时未使用
from app.infra.repositories import TtsJobRepository
from app.infra.queue import get_queue_manager
from app.db_conn import get_db_conn
import sqlite3

router = APIRouter()

@router.post(
    "/tts/jobs",
    summary="提交 TTS 任务（入队）",
    tags=["TTS Jobs"],
    response_model=oc8r.TtsJobResponse,
    status_code=status.HTTP_202_ACCEPTED
)
async def create_tts_job(
    body: oc8r.CreateTtsJobRequest,
    db: sqlite3.Connection = Depends(get_db_conn)
):
    """
    提交 TTS 任务，入队并返回 202 TtsJobResponse（状态为 queued）
    - 当前为占位实现，仅返回模拟数据
    """
    job_repo = TtsJobRepository(db)
    now = datetime.now().isoformat()
    # 入队占位 payload（后续由策略构建完整 payload）
    qm = get_queue_manager()
    job_id = await qm.enqueue({
        "request": body.model_dump(mode='json'),
        "createdAt": now,
    })
    job = oc8r.TtsJob(
        id=job_id,
        type=oc8r.Type.tts,
        status=oc8r.JobStatus.queued,
        createdAt=now,
        updatedAt=now,
        request=body,
        result=None,
        error=None
    )
    # 持久化入库（queued 状态）
    job_repo.add(job)
    resp = oc8r.TtsJobResponse(
        code=202,
        message="Job queued",
        job=job
    )
    return JSONResponse(status_code=202, content=resp.model_dump(mode='json'))


@router.get(
    "/tts/jobs/{job_id}",
    summary="查询 TTS 任务（占位）",
    tags=["TTS Jobs"],
    response_model=oc8r.TtsJobResponse,
    status_code=status.HTTP_200_OK
)
async def get_tts_job(
    job_id: str,
    db: sqlite3.Connection = Depends(get_db_conn)
):
    """
    查询 TTS 任务（占位实现，后续完善实际逻辑）
    """
    job_repo = TtsJobRepository(db)
    job = job_repo.get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    resp = oc8r.TtsJobResponse(
        code=200,
        message="Job found",
        job=job
    )
    return JSONResponse(status_code=200, content=resp.model_dump(mode='json'))

@router.get(
    "/tts/jobs",
    summary="查询 TTS 任务",
    tags=["TTS Jobs"],
    response_model=oc8r.TtsJobListResponse,
    status_code=status.HTTP_200_OK
)
async def list_tts_jobs(db: sqlite3.Connection = Depends(get_db_conn)):
    """
    查询 TTS 任务
    """
    job_repo = TtsJobRepository(db)
    jobs = job_repo.list()
    resp = oc8r.TtsJobListResponse(
        code=200,
        message="Jobs found",
        jobs=jobs
    )
    return JSONResponse(status_code=200, content=resp.model_dump(mode='json'))

@router.post(
    "/tts/jobs/{job_id}/cancel",
    summary="取消 TTS 任务",
    tags=["TTS Jobs"],
    response_model=oc8r.TtsJobResponse,
    status_code=status.HTTP_200_OK
)
async def cancel_tts_job(
    job_id: str,
    db: sqlite3.Connection = Depends(get_db_conn)
):
    """
    取消 TTS 任务
    - 检查任务是否存在
    - 如果任务在队列中，从队列中移除
    - 更新任务状态为cancelled
    """
    job_repo = TtsJobRepository(db)
    job = job_repo.get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    # 检查任务状态，只有queued和running状态可以取消
    if job.status not in [oc8r.JobStatus.queued, oc8r.JobStatus.running]:
        raise HTTPException(status_code=400, detail="Job cannot be cancelled in current status")
    
    # 从队列中取消任务
    qm = get_queue_manager()
    await qm.cancel(job_id)
    
    # 更新数据库状态
    job_repo.update(
        job_id,
        status=oc8r.JobStatus.cancelled,
        updatedAt=datetime.now().isoformat()
    )
    
    # 重新获取更新后的任务
    updated_job = job_repo.get(job_id)
    resp = oc8r.TtsJobResponse(
        code=200,
        message="Job cancelled successfully",
        job=updated_job
    )
    return JSONResponse(status_code=200, content=resp.model_dump(mode='json'))

@router.post(
    "/tts/jobs/{job_id}/retry",
    summary="重试 TTS 任务",
    tags=["TTS Jobs"],
    response_model=oc8r.TtsJobResponse,
    status_code=status.HTTP_201_CREATED
)
async def retry_tts_job(
    job_id: str,
    db: sqlite3.Connection = Depends(get_db_conn)
):
    """
    重试 TTS 任务
    - 检查原任务是否存在且状态为failed
    - 创建新的任务记录，复制原请求参数
    - 将新任务加入队列
    """
    job_repo = TtsJobRepository(db)
    original_job = job_repo.get(job_id)
    if not original_job:
        raise HTTPException(status_code=404, detail="Original job not found")
    
    # 只有失败的任务可以重试
    if original_job.status != oc8r.JobStatus.failed:
        raise HTTPException(status_code=400, detail="Only failed jobs can be retried")
    
    # 创建新的任务记录
    now = datetime.now().isoformat()
    new_job_id = str(uuid.uuid4())
    new_job = oc8r.TtsJob(
        id=new_job_id,
        type=original_job.type,
        status=oc8r.JobStatus.queued,
        createdAt=now,
        updatedAt=now,
        request=original_job.request,
        result=None,
        error=None
    )
    
    # 保存新任务到数据库
    job_repo.add(new_job)
    
    # 将新任务加入队列
    qm = get_queue_manager()
    await qm.enqueue({
        "request": original_job.request.model_dump(mode='json'),
        "createdAt": now,
    })
    
    resp = oc8r.TtsJobResponse(
        code=201,
        message="Job retry created successfully",
        job=new_job
    )
    return JSONResponse(status_code=201, content=resp.model_dump(mode='json'))
