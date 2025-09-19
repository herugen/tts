"""
文件级注释：
本模块为应用入口，负责创建 FastAPI 实例，并挂载 API 路由前缀。遵循分层架构原则，接口层仅处理路由注册和基础响应。

背景说明：
- 采用 FastAPI 框架，便于后续扩展和自动文档生成。
- 所有 API 路由统一挂载在 /api/v1 前缀下，便于版本管理。
- 使用ApplicationContainer统一管理所有应用服务的依赖注入。

架构说明：
- 仅包含接口层逻辑，业务逻辑与基础设施后续分离。
- 数据库连接管理委托给 app.db_conn 模块。
- 应用服务通过ApplicationContainer统一管理，确保依赖注入的一致性。
"""

from fastapi import FastAPI, HTTPException
from fastapi.exceptions import RequestValidationError
from contextlib import asynccontextmanager
from app.api import health
from app.api import uploads
from app.api import queue
from app.api import voices
from app.api import jobs
from app.api import audio
from app.db_conn import startup, shutdown
from app.middleware import (
    http_exception_handler,
    validation_exception_handler,
    general_exception_handler,
)
from app.container import app_container
import logging

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(_: FastAPI):
    """应用生命周期管理"""
    # 启动时执行
    await startup()

    # 初始化应用服务容器
    logger.info("Initializing application services...")
    # 预初始化所有服务，确保依赖关系正确
    app_container.get_all_services()
    logger.info("Application services initialized successfully")

    # 获取队列应用服务并启动队列处理
    queue_service = app_container.get_queue_service()
    await queue_service.start_processing()
    logger.info("Queue processing started")

    yield

    # 关闭时执行
    await queue_service.stop_processing()
    logger.info("Queue processing stopped")
    await shutdown()


# 创建 FastAPI 应用并挂载路由
app = FastAPI(lifespan=lifespan)

# 注册错误处理中间件
app.add_exception_handler(HTTPException, http_exception_handler)
app.add_exception_handler(RequestValidationError, validation_exception_handler)
app.add_exception_handler(Exception, general_exception_handler)

# 注册路由
app.include_router(health.router, prefix="/api/v1")
app.include_router(uploads.router, prefix="/api/v1")
app.include_router(queue.router, prefix="/api/v1")
app.include_router(voices.router, prefix="/api/v1")
app.include_router(jobs.router, prefix="/api/v1")
app.include_router(audio.router, prefix="/api/v1")
