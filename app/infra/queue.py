"""
文件级注释：
本模块属于基础设施层（Infrastructure Layer），负责实现队列管理与异步任务 worker 的纯技术实现。
- QueueManager 提供任务入队（enqueue）和状态查询（status）接口，支持后续扩展多种队列后端（如 Redis、RabbitMQ）。
- Worker 采用 asyncio 协程方式，应用启动时通过 asyncio.create_task 启动后台任务消费队列。
- 仅提供纯技术实现，不包含任何业务逻辑，具体任务处理逻辑由上层注入。

架构说明：
- 队列采用内存队列（asyncio.Queue）实现，便于开发测试，后续可替换为分布式队列。
- 任务状态存储于内存字典，生产环境建议持久化。
- 遵循高内聚低耦合，队列与 worker 解耦，便于扩展和测试。
- 纯技术实现，不包含业务逻辑，业务逻辑由应用层处理。

依赖说明：
- 仅依赖 Python 标准库 asyncio、uuid、typing
- 不依赖业务模型和业务逻辑
"""

import asyncio
import uuid
import logging
from typing import Any, Dict, Optional, Callable
from app.models import oc8r

logger = logging.getLogger(__name__)



class QueueManager:
    """
    队列管理器 - 纯技术实现
    
    负责任务入队、状态查询，支持后续扩展多种队列后端。
    """

    def __init__(self):
        """
        初始化内存队列和任务状态字典。
        """
        self.queue = asyncio.Queue()
        self.status_map: Dict[str, Dict[str, Any]] = {}
        self.status_callback: Optional[Callable] = None
        self.current_task_id: Optional[str] = None

    def set_callback(self, status_callback: Callable):
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

    def __init__(self, queue_mgr: QueueManager, handler: Callable):
        """
        :param queue_mgr: 队列管理器实例
        :param handler: 任务处理函数，签名为 async def handler(payload) -> result
        """
        self.queue_manager = queue_mgr
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
                logger.error("Task processing failed: %s", str(e))
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

async def _default_task_handler(_payload: Any) -> Any:
    """
    默认任务处理器（占位实现）
    实际项目中应该根据任务类型分发到对应的处理器
    """
    # 最小占位：模拟处理耗时
    await asyncio.sleep(0.05)
    return {"ok": True, "message": "Default handler processed task"}

async def start_queue(task_handler: Callable = None) -> None:
    """
    启动队列
    
    Args:
        task_handler: 任务处理器，由应用层注入
    """
    global _worker, _worker_task
    if _worker_task is not None:
        return
    
    # 使用注入的处理器或默认处理器
    handler = task_handler or _default_task_handler
    _worker = Worker(queue_manager, handler)
    _worker_task = asyncio.create_task(_worker.run())

async def stop_queue() -> None:
    """
    停止队列
    """
    global _worker, _worker_task
    if _worker is not None:
        _worker.stop()
    if _worker_task is not None:
        _worker_task.cancel()
        try:
            await _worker_task
        except asyncio.CancelledError:
            # 忽略取消异常
            pass
    _worker = None
    _worker_task = None


def get_queue_manager() -> QueueManager:
    return queue_manager
