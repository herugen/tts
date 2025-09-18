"""
文件级注释：
本模块属于基础设施层（Infrastructure Layer），负责实现队列管理与异步任务 worker 的基础骨架。
- QueueManager 提供任务入队（enqueue）和状态查询（status）接口，支持后续扩展多种队列后端（如 Redis、RabbitMQ）。
- Worker 采用 asyncio 协程方式，应用启动时通过 asyncio.create_task 启动后台任务消费队列。
- 仅提供基础骨架，具体任务类型、处理逻辑由上层注入或扩展。

架构说明：
- 队列采用内存队列（asyncio.Queue）实现，便于开发测试，后续可替换为分布式队列。
- 任务状态存储于内存字典，生产环境建议持久化。
- 遵循高内聚低耦合，队列与 worker 解耦，便于扩展和测试。

依赖说明：
- 仅依赖 Python 标准库 asyncio、uuid、typing
"""

import asyncio
import uuid
import logging
from typing import Any, Dict, Optional
from app.models import oc8r
from app.infra.repositories import TtsJobRepository
from app.db_conn import get_db_conn
from datetime import datetime

logger = logging.getLogger(__name__)


class JobStatusCallback:
    """
    JobStatusCallback
    -----------------
    TTS 任务状态变更回调器，根据状态执行持久化操作。
    """

    def __init__(self, job_repo: TtsJobRepository):
        """
        初始化回调器，注入 TtsJobRepository
        """
        self.job_repo = job_repo

    async def on_status_change(
        self,
        job_id: str,
        new_status: oc8r.JobStatus,
        result: Optional[Any] = None,
    ):
        """
        统一入口：根据新状态分发到对应处理方法
        """
        updated_at = datetime.now().isoformat()
        handler = self._get_handler(new_status)
        await handler(job_id=job_id, updated_at=updated_at, result=result)

    def _get_handler(self, new_status: oc8r.JobStatus):
        """
        策略分发：根据状态返回对应处理方法
        """
        return {
            oc8r.JobStatus.queued: self._handle_queued,
            oc8r.JobStatus.running: self._handle_running,
            oc8r.JobStatus.succeeded: self._handle_succeeded,
            oc8r.JobStatus.failed: self._handle_failed,
            oc8r.JobStatus.cancelled: self._handle_cancelled
        }.get(new_status, self._handle_unknown)

    async def _handle_queued(self, job_id: str, **kwargs):
        """
        处理 queued 状态：仅更新状态和更新时间
        """
        self.job_repo.update(
            job_id,
            status=oc8r.JobStatus.queued,
            updatedAt=kwargs.get("updated_at")
        )

    async def _handle_running(self, job_id: str, **kwargs):
        """
        处理 processing 状态：仅更新状态和更新时间
        """
        self.job_repo.update(
            job_id,
            status=oc8r.JobStatus.running,
            updatedAt=kwargs.get("updated_at")
        )

    async def _handle_succeeded(self, job_id: str, **kwargs):
        """
        处理 succeeded 状态：更新状态、结果和更新时间
        """
        result_data = kwargs.get("result", {})
        result = oc8r.Result(
            audioUrl=result_data.get("audioUrl"),
            durationSeconds=result_data.get("durationSeconds"),
            format=result_data.get("format")
        )
        self.job_repo.update(
            job_id,
            status=oc8r.JobStatus.succeeded,
            result=result,
            updatedAt=kwargs.get("updated_at")
        )

    async def _handle_failed(self, job_id: str, **kwargs):
        """
        处理 failed 状态：更新状态、错误信息和更新时间
        """
        error_message = str(kwargs.get("result", "Unknown error"))
        error = oc8r.ErrorResponse(
            code="TTS_PROCESSING_FAILED",
            message=error_message
        )
        self.job_repo.update(
            job_id,
            status=oc8r.JobStatus.failed,
            error=error,
            updatedAt=kwargs.get("updated_at")
        )

    async def _handle_cancelled(self, job_id: str, **kwargs):
        """
        处理 cancelled 状态：仅更新状态和更新时间
        """
        self.job_repo.update(
            job_id,
            status=oc8r.JobStatus.cancelled,
            updatedAt=kwargs.get("updated_at")
        )

    async def _handle_unknown(self, job_id: str, **kwargs):
        """
        处理未知状态：不做任何操作
        """
        logger.warning(f"Unknown job status for job {job_id}")

class QueueManager:
    """
    队列管理器
    负责任务入队、状态查询，支持后续扩展多种队列后端。
    """

    def __init__(self):
        """
        初始化内存队列和任务状态字典。
        """
        self.queue = asyncio.Queue()
        self.status_map: Dict[str, Dict[str, Any]] = {}
        self.status_callback = None
        self.current_task_id = None


    def set_callback(self, status_callback: Any):
        """
        设置任务状态变更回调函数。
        :param status_callback: 任务状态变更回调函数
        """
        self.status_callback = status_callback

    async def enqueue(self, payload: Any) -> str:
        """
        入队一个任务，返回任务ID。
        :param payload: 任务数据
        :return: 任务ID
        """
        task_id = str(uuid.uuid4())
        task = {
            "id": task_id,
            "payload": payload
        }
        await self.queue.put(task)
        self.status_map[task_id] = {}
        await self.set_status(task_id, oc8r.JobStatus.queued)
        return task_id

    def status(self, task_id: str) -> Dict[str, Any]:
        """
        查询任务状态。
        :param task_id: 任务ID
        :return: 状态字典
        """
        return self.status_map.get(task_id, {"status": "not_found", "result": None})

    async def set_status(self, task_id: str, status: oc8r.JobStatus, result: Optional[Any] = None):
        """
        更新任务状态。
        :param task_id: 任务ID
        :param status: 状态
        :param result: 结果数据
        """
        self.status_map[task_id]["status"] = status
        self.status_map[task_id]["result"] = result
        if self.status_callback is not None:
            await self.status_callback(job_id=task_id, status=status, result=result)

    async def cancel(self, task_id: str):
        """
        取消任务。
        :param task_id: 任务ID
        """
        # 确保任务ID在状态映射中存在
        if task_id not in self.status_map:
            self.status_map[task_id] = {}
        await self.set_status(task_id, oc8r.JobStatus.cancelled)

    async def retry(self, task_id: str, payload: Any):
        """
        重试任务。
        :param task_id: 任务ID
        """
        task = {
            "id": task_id,
            "payload": payload
        }
        await self.queue.put(task)
        await self.set_status(task_id, oc8r.JobStatus.queued)

    def running_job_id(self) -> Optional[str]:
        """
        获取正在运行的任务ID。
        :return: 正在运行的任务ID
        """
        return self.current_task_id
    
    def queue_length(self) -> int:
        """
        获取队列长度。
        :return: 队列长度
        """
        return self.queue.qsize()

class Worker:
    """
    单 worker 协程，持续消费队列任务并处理。
    """

    def __init__(self, queue_manager: QueueManager, handler):
        """
        :param queue_manager: 队列管理器实例
        :param handler: 任务处理函数，签名为 async def handler(payload) -> result
        """
        self.queue_manager = queue_manager
        self.handler = handler
        self._running = False

    async def run(self):
        """
        持续消费队列任务，处理并更新状态。
        """
        self._running = True
        while self._running:
            task = await self.queue_manager.queue.get()
            task_id = task["id"]
            payload = task["payload"]
            try:
                if self.queue_manager.status(task_id).get("status") == oc8r.JobStatus.cancelled:
                    continue
                self.queue_manager.current_task_id = task_id
                await self.queue_manager.set_status(task_id, oc8r.JobStatus.running)
                result = await self.handler(payload)
                await self.queue_manager.set_status(task_id, oc8r.JobStatus.succeeded, result)
            except Exception as e:
                await self.queue_manager.set_status(task_id, oc8r.JobStatus.failed, str(e))
            finally:
                self.queue_manager.current_task_id = None
                self.queue_manager.queue.task_done()

    def stop(self):
        """
        停止 worker 循环（需外部协程取消）。
        """
        self._running = False

# ---- 应用级单例与启动/停止钩子 ----

queue_manager = QueueManager()
_worker: Optional[Worker] = None
_worker_task: Optional[asyncio.Task] = None

async def _default_task_handler(payload: Any) -> Any:
    """
    默认任务处理器（占位实现）
    实际项目中应该根据任务类型分发到对应的处理器
    """
    # 最小占位：模拟处理耗时
    await asyncio.sleep(0.05)
    return {"ok": True}

async def _tts_task_handler(payload: Any) -> Any:
    """
    TTS任务处理器
    根据请求模式选择对应的策略进行TTS合成
    """
    from app.domain.strategies.tts_strategy import TtsStrategyFactory
    from app.infra.indextts_client import IndexTtsClient
    from app.infra.repositories import VoiceRepository, UploadRepository
    from app.infra.storage import LocalFileStorage
    from app.db_conn import get_db_conn
    
    try:
        # 解析请求数据
        request_data = payload.get("request", {})
        request = oc8r.CreateTtsJobRequest(**request_data)
        
        # 获取数据库连接和仓库
        db_conn = get_db_conn()
        voice_repo = VoiceRepository(db_conn)
        upload_repo = UploadRepository(db_conn)
        storage = LocalFileStorage()
        
        # 创建IndexTTS客户端
        client = IndexTtsClient()
        
        try:
            # 根据模式创建策略
            strategy = TtsStrategyFactory.create_strategy(
                request.mode, 
                client, 
                voice_repo, 
                upload_repo, 
                storage
            )
            
            # 验证请求参数
            await strategy.validate_request(request)
            
            # 执行TTS合成
            result = await strategy.synthesize(request)
            
            return result
            
        finally:
            # 确保客户端被正确关闭
            await client.close()
            
    except Exception as e:
        logger.error(f"TTS task processing failed: {str(e)}")
        raise


async def start_queue() -> None:
    global _worker, _worker_task
    if _worker_task is not None:
        return
    _worker = Worker(queue_manager, _tts_task_handler)
    _worker_task = asyncio.create_task(_worker.run())

    # 获取全局数据库连接
    db_conn = get_db_conn()
    job_repo = TtsJobRepository(db_conn)
    job_status_callback = JobStatusCallback(job_repo=job_repo)
    queue_manager.set_callback(job_status_callback.on_status_change)

async def stop_queue() -> None:
    global _worker, _worker_task
    if _worker is not None:
        _worker.stop()
    if _worker_task is not None:
        _worker_task.cancel()
        try:
            await _worker_task
        except Exception:
            # 忽略取消异常
            pass
    _worker = None
    _worker_task = None


def get_queue_manager() -> QueueManager:
    return queue_manager
