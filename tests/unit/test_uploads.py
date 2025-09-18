"""
文件上传端点测试
测试 /uploads 端点的功能
"""

import pytest
from fastapi import status
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
import tempfile
import os

class TestUploadEndpoint:
    """文件上传端点测试类"""
    
    def test_upload_audio_success(self, test_client, sample_audio_file):
        """测试音频文件上传成功"""
        with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as temp_file:
            temp_file.write(sample_audio_file)
            temp_file.flush()
            
            with open(temp_file.name, 'rb') as f:
                response = test_client.post(
                    "/api/v1/uploads",
                    files={"file": ("test.wav", f, "audio/wav")}
                )
            
            os.unlink(temp_file.name)
        
        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert "upload" in data
        assert data["upload"]["fileName"] == "test.wav"
        assert data["upload"]["contentType"] == "audio/wav"
        assert data["upload"]["sizeBytes"] > 0
        assert "id" in data["upload"]
        assert "createdAt" in data["upload"]
    
    def test_upload_unsupported_file_type(self, test_client):
        """测试不支持的文件类型"""
        with tempfile.NamedTemporaryFile(suffix='.txt', delete=False) as temp_file:
            temp_file.write(b"test content")
            temp_file.flush()
            
            with open(temp_file.name, 'rb') as f:
                response = test_client.post(
                    "/api/v1/uploads",
                    files={"file": ("test.txt", f, "text/plain")}
                )
            
            os.unlink(temp_file.name)
        
        assert response.status_code == status.HTTP_415_UNSUPPORTED_MEDIA_TYPE
    
    def test_upload_file_too_large(self, test_client):
        """测试文件过大"""
        # 创建一个超过限制的文件（模拟）
        large_content = b"x" * (21 * 1024 * 1024)  # 21MB
        
        with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as temp_file:
            temp_file.write(large_content)
            temp_file.flush()
            
            with open(temp_file.name, 'rb') as f:
                response = test_client.post(
                    "/api/v1/uploads",
                    files={"file": ("large.wav", f, "audio/wav")}
                )
            
            os.unlink(temp_file.name)
        
        assert response.status_code == status.HTTP_413_CONTENT_TOO_LARGE
    
    def test_upload_missing_file(self, test_client):
        """测试缺少文件参数"""
        response = test_client.post("/api/v1/uploads")
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT
    
    def test_upload_response_format(self, test_client, sample_audio_file):
        """测试上传响应格式"""
        with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as temp_file:
            temp_file.write(sample_audio_file)
            temp_file.flush()
            
            with open(temp_file.name, 'rb') as f:
                response = test_client.post(
                    "/api/v1/uploads",
                    files={"file": ("test.wav", f, "audio/wav")}
                )
            
            os.unlink(temp_file.name)
        
        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        
        # 验证响应结构
        assert "code" in data
        assert "message" in data
        assert "upload" in data
        
        upload = data["upload"]
        required_fields = ["id", "fileName", "contentType", "sizeBytes", "createdAt"]
        for field in required_fields:
            assert field in upload
    
    def test_upload_mp3_file(self, test_client):
        """测试MP3文件上传"""
        mp3_content = b"ID3\x03\x00\x00\x00\x00\x00\x00\x00"  # 简单的MP3头
        
        with tempfile.NamedTemporaryFile(suffix='.mp3', delete=False) as temp_file:
            temp_file.write(mp3_content)
            temp_file.flush()
            
            with open(temp_file.name, 'rb') as f:
                response = test_client.post(
                    "/api/v1/uploads",
                    files={"file": ("test.mp3", f, "audio/mpeg")}
                )
            
            os.unlink(temp_file.name)
        
        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert data["upload"]["fileName"] == "test.mp3"
        assert data["upload"]["contentType"] == "audio/mpeg"
