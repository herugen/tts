"""
Queue应用服务

处理队列相关的业务协调，包括：
- 查询队列状态
- 启动和停止队列处理
- 协调队列和业务处理器

职责：
- 协调领域对象和基础设施层
- 处理队列状态相关的用例
- 协调队列消费和业务处理
- 不包含具体的业务逻辑
"""

import asyncio
import logging
from typing import Optional, Any, Callable
from app.models.oc8r import QueueStatus, JobStatus
from app.infra.queue import QueueManager

logger = logging.getLogger(__name__)


class QueueWorker:
    """
    队列工作器 - 应用层组件

    负责消费队列任务并调用业务处理器，属于应用层协调组件。
    将队列消费逻辑与业务处理逻辑协调起来。
    """

    def __init__(self, queue_mgr: QueueManager, handler: Callable[[Any], Any]):
        """
        初始化队列工作器

        Args:
            queue_mgr: 队列管理器实例
            handler: 任务处理函数，签名为 async def handler(payload) -> result
        """
        self.queue_manager = queue_mgr
        self.handler = handler
        self._running = False

    async def run(self):
        """
        持续消费队列任务，处理并更新状态
        """
        self._running = True
        while self._running:
            task = await self.queue_manager.queue.get()
            task_id = task["id"]
            payload = task["payload"]
            try:
                if (
                    self.queue_manager.status(task_id).get("status")
                    == JobStatus.cancelled
                ):
                    continue
                self.queue_manager.current_task_id = task_id
                await self.queue_manager.set_status(task_id, JobStatus.running)
                result = await self.handler(payload)
                await self.queue_manager.set_status(
                    task_id, JobStatus.succeeded, result
                )

            except Exception as e:
                logger.error("Task processing failed: %s", str(e))
                await self.queue_manager.set_status(task_id, JobStatus.failed, str(e))
            finally:
                self.queue_manager.current_task_id = None
                self.queue_manager.queue.task_done()

    def stop(self):
        """
        停止 worker 循环（需外部协程取消）
        """
        self._running = False


class QueueApplicationService:
    """
    Queue应用服务

    负责协调队列相关的业务用例，包括队列状态查询、队列处理启动和停止等操作。
    作为接口层和领域层之间的桥梁，只做业务协调，不包含具体业务逻辑。
    """

    def __init__(self, queue_manager: QueueManager, tts_processor):
        """
        初始化Queue应用服务

        Args:
            queue_manager: 队列管理器
            tts_processor: TTS处理器，用于处理队列中的任务
        """
        self.queue_manager = queue_manager
        self.tts_processor = tts_processor
        self.worker: Optional[QueueWorker] = None
        self._worker_task: Optional[asyncio.Task] = None

    async def get_status(self) -> QueueStatus:
        """
        获取队列状态

        Returns:
            QueueStatus: 队列状态对象
        """
        # 构建队列状态对象
        queue_status = QueueStatus(
            maxConcurrency=1,
            runningJobId=self.queue_manager.running_job_id(),
            queueLength=self.queue_manager.queue_length(),
            averageWaitSeconds=None,
        )

        return queue_status

    async def start_processing(self):
        """
        启动队列处理

        创建Worker实例并启动后台任务处理队列中的任务
        """
        if self._worker_task is not None:
            return  # 已经在运行

        # 创建Worker实例，注入TTS处理器
        self.worker = QueueWorker(self.queue_manager, self.tts_processor.process)
        self._worker_task = asyncio.create_task(self.worker.run())

    async def stop_processing(self):
        """
        停止队列处理

        停止Worker并清理相关资源
        """
        if self.worker is not None:
            self.worker.stop()

        if self._worker_task is not None:
            self._worker_task.cancel()
            try:
                await self._worker_task
            except asyncio.CancelledError:
                # 忽略取消异常
                pass

        self.worker = None
        self._worker_task = None

    def is_processing(self) -> bool:
        """
        检查是否正在处理队列

        Returns:
            bool: 是否正在处理
        """
        return self._worker_task is not None and not self._worker_task.done()
