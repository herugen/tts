"""
文件级注释：
本模块负责实现 /health 健康检查接口，属于接口层（Interface Layer）。
遵循分层架构原则，接口层仅处理 HTTP 请求和响应组装，不涉及具体健康检测逻辑（如数据库、外部服务等）。
如需扩展健康检查内容，可通过依赖注入方式引入检测服务。

接口说明：
- 路由: GET /health
- 响应: HealthResponse（见 tts_oc8r.yml components/schemas/HealthResponse）
- 仅返回静态健康状态，后续可扩展为动态检测

依赖说明：
- 无外部依赖，仅返回静态响应
"""

from fastapi import APIRouter, status
from fastapi.responses import JSONResponse

router = APIRouter()


@router.get(
    "/health", summary="健康检查", tags=["Health"], status_code=status.HTTP_200_OK
)
async def health_check():
    """
    健康检查接口
    - 返回 HealthResponse 格式，包含 code 和 message 字段
    - 目前仅返回静态 OK 状态
    """
    resp = {"code": 200, "message": "OK"}
    return JSONResponse(status_code=200, content=resp)
