"""
Queue应用服务

处理队列状态相关的业务协调，包括：
- 查询队列状态

职责：
- 协调领域对象和基础设施层
- 处理队列状态相关的用例
- 不包含具体的业务逻辑
"""

from app.models.oc8r import QueueStatus
from app.infra.queue import QueueManager


class QueueApplicationService:
    """
    Queue应用服务

    负责协调队列状态相关的业务用例，包括队列状态查询等操作。
    作为接口层和领域层之间的桥梁，只做业务协调，不包含具体业务逻辑。
    """

    def __init__(self, queue_manager: QueueManager):
        """
        初始化Queue应用服务

        Args:
            queue_manager: 队列管理器
        """
        self.queue_manager = queue_manager

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
