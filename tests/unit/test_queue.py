"""
队列状态端点测试
测试 /queue/status 端点的功能
"""

from fastapi import status
from unittest.mock import patch, MagicMock

class TestQueueEndpoint:
    """队列状态端点测试类"""
    
    def test_get_queue_status_success(self, test_client):
        """测试获取队列状态成功"""
        response = test_client.get("/api/v1/queue/status")
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "status" in data
        assert "code" in data
        assert "message" in data
        
        status_data = data["status"]
        assert "maxConcurrency" in status_data
        assert "queueLength" in status_data
        assert status_data["maxConcurrency"] == 1
    
    def test_get_queue_status_response_format(self, test_client):
        """测试队列状态响应格式"""
        response = test_client.get("/api/v1/queue/status")
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        
        # 验证响应结构
        assert data["code"] == 200
        assert data["message"] == "OK"
        
        status_data = data["status"]
        required_fields = ["maxConcurrency", "queueLength"]
        for field in required_fields:
            assert field in status_data
            assert isinstance(status_data[field], int)
    
    def test_get_queue_status_with_running_job(self, test_client):
        """测试有运行中任务时的队列状态"""
        with patch('app.container.app_container.get_queue_service') as mock_get_queue_service:
            mock_queue_service = MagicMock()
            # 创建mock的QueueStatus对象
            from app.models.oc8r import QueueStatus
            mock_status = QueueStatus(
                maxConcurrency=1,
                runningJobId="running-job-123",
                queueLength=3,
                averageWaitSeconds=None
            )
            # 使用AsyncMock来模拟异步方法
            from unittest.mock import AsyncMock
            mock_queue_service.get_status = AsyncMock(return_value=mock_status)
            mock_get_queue_service.return_value = mock_queue_service
            
            response = test_client.get("/api/v1/queue/status")
            
            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            status_data = data["status"]
            assert status_data["runningJobId"] == "running-job-123"
            assert status_data["queueLength"] == 3
    
    def test_get_queue_status_empty_queue(self, test_client):
        """测试空队列状态"""
        with patch('app.container.app_container.get_queue_service') as mock_get_queue_service:
            mock_queue_service = MagicMock()
            # 创建mock的QueueStatus对象
            from app.models.oc8r import QueueStatus
            mock_status = QueueStatus(
                maxConcurrency=1,
                runningJobId=None,
                queueLength=0,
                averageWaitSeconds=None
            )
            # 使用AsyncMock来模拟异步方法
            from unittest.mock import AsyncMock
            mock_queue_service.get_status = AsyncMock(return_value=mock_status)
            mock_get_queue_service.return_value = mock_queue_service
            
            response = test_client.get("/api/v1/queue/status")
            
            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            status_data = data["status"]
            assert status_data["runningJobId"] is None
            assert status_data["queueLength"] == 0
    
    def test_get_queue_status_content_type(self, test_client):
        """测试队列状态内容类型"""
        response = test_client.get("/api/v1/queue/status")
        
        assert response.status_code == status.HTTP_200_OK
        assert response.headers["content-type"] == "application/json"
