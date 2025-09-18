"""
队列状态端点测试
测试 /queue/status 端点的功能
"""

import pytest
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
        with patch('app.api.queue.get_queue_manager') as mock_get_queue:
            mock_queue_manager = MagicMock()
            # 修复：设置方法返回值而不是属性
            mock_queue_manager.running_job_id.return_value = "running-job-123"
            mock_queue_manager.queue_length.return_value = 3
            mock_get_queue.return_value = mock_queue_manager
            
            response = test_client.get("/api/v1/queue/status")
            
            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            status_data = data["status"]
            assert status_data["runningJobId"] == "running-job-123"
            assert status_data["queueLength"] == 3
    
    def test_get_queue_status_empty_queue(self, test_client):
        """测试空队列状态"""
        with patch('app.api.queue.get_queue_manager') as mock_get_queue:
            mock_queue_manager = MagicMock()
            mock_queue_manager.running_job_id.return_value = None
            mock_queue_manager.queue_length.return_value = 0
            mock_get_queue.return_value = mock_queue_manager
            
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
