"""
健康检查端点测试
测试 /health 端点的功能
"""

import pytest
from fastapi import status


class TestHealthEndpoint:
    """健康检查端点测试类"""

    def test_health_check_success(self, test_client):
        """测试健康检查成功响应"""
        response = test_client.get("/api/v1/health")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["code"] == 200
        assert data["message"] == "OK"

    def test_health_check_response_format(self, test_client):
        """测试健康检查响应格式"""
        response = test_client.get("/api/v1/health")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        # 验证响应字段
        assert "code" in data
        assert "message" in data
        assert isinstance(data["code"], int)
        assert isinstance(data["message"], str)

    def test_health_check_content_type(self, test_client):
        """测试健康检查内容类型"""
        response = test_client.get("/api/v1/health")

        assert response.status_code == status.HTTP_200_OK
        assert response.headers["content-type"] == "application/json"
