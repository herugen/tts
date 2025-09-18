"""
文件级注释：
本模块实现全局错误处理中间件，统一处理应用中的异常并返回标准化的错误响应。
遵循分层架构原则，中间件层负责统一异常处理，确保所有错误都符合OpenAPI规范。

架构说明：
- 捕获HTTPException、ValidationError等常见异常
- 统一转换为ErrorResponse格式
- 记录错误日志便于调试
- 支持不同HTTP状态码的错误处理

依赖说明：
- 依赖FastAPI的异常处理机制
- 依赖app.models.oc8r.ErrorResponse模型
"""

from fastapi import Request, HTTPException
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from app.models import oc8r
import logging

logger = logging.getLogger(__name__)


async def http_exception_handler(request: Request, exc: HTTPException):
    """
    处理HTTPException异常
    """
    error_response = oc8r.ErrorResponse(code=str(exc.status_code), message=exc.detail)
    logger.warning(f"HTTP Exception: {exc.status_code} - {exc.detail}")
    return JSONResponse(
        status_code=exc.status_code, content=error_response.model_dump()
    )


async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """
    处理请求验证异常
    """
    error_details = []
    for error in exc.errors():
        field = " -> ".join(str(loc) for loc in error["loc"])
        message = error["msg"]
        error_details.append(f"{field}: {message}")

    error_message = "; ".join(error_details)
    error_response = oc8r.ErrorResponse(
        code="VALIDATION_ERROR", message=f"Request validation failed: {error_message}"
    )
    logger.warning(f"Validation Error: {error_message}")
    return JSONResponse(status_code=422, content=error_response.model_dump())


async def general_exception_handler(request: Request, exc: Exception):
    """
    处理通用异常
    """
    error_response = oc8r.ErrorResponse(
        code="INTERNAL_SERVER_ERROR", message="An unexpected error occurred"
    )
    logger.error(f"Unhandled exception: {str(exc)}", exc_info=True)
    return JSONResponse(status_code=500, content=error_response.model_dump())
