"""
文件级注释：
本模块负责实现 /queue/status 队列状态查询接口，属于接口层（Interface Layer）。
当前为静态占位实现，返回固定的队列状态信息，后续可对接实际队列管理逻辑。

接口说明：
- 路由: GET /queue/status
- 响应: QueueStatusResponse（见 app/models/oc8r.py）
- 当前返回 maxConcurrency=1，queueLength=0，runningJobId=None，averageWaitSeconds=None

依赖说明：
- 依赖 oc8r.QueueStatusResponse/QueueStatus 组装响应体
"""

from fastapi import APIRouter, status, Depends
from fastapi.responses import JSONResponse
from app.models import oc8r
from app.dependencies import get_queue_service
from app.application.queue_service import QueueApplicationService

router = APIRouter()


@router.get(
    "/queue/status",
    summary="查询队列状态",
    tags=["Queue"],
    response_model=oc8r.QueueStatusResponse,
    status_code=status.HTTP_200_OK,
)
async def get_queue_status(
    queue_service: QueueApplicationService = Depends(get_queue_service),
):
    """
    查询队列状态接口
    - 委托给Queue应用服务处理业务逻辑
    """
    # 委托给Queue应用服务获取队列状态
    status_obj = await queue_service.get_status()

    resp = oc8r.QueueStatusResponse(code=200, message="OK", status=status_obj)
    return JSONResponse(status_code=200, content=resp.model_dump())
