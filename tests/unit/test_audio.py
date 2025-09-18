"""
音频文件服务端点测试
测试 /audio/{filename} 端点的功能
"""

import os
import pytest
from fastapi import status


class TestAudioEndpoint:
    """音频文件服务端点测试类"""

    @pytest.fixture(autouse=True)
    def setup_test_environment(self, test_client):
        """测试环境设置"""
        self.client = test_client
        # 确保输出目录存在
        self.output_dir = "data/outputs"
        os.makedirs(self.output_dir, exist_ok=True)

    def test_get_audio_file_success(self):
        """测试获取音频文件成功"""
        # 创建一个测试音频文件
        test_filename = "test_audio.wav"
        test_file_path = os.path.join(self.output_dir, test_filename)

        # 创建测试文件内容
        test_content = b"fake wav file content"
        with open(test_file_path, "wb") as f:
            f.write(test_content)

        try:
            response = self.client.get(f"/api/v1/audio/{test_filename}")

            assert response.status_code == status.HTTP_200_OK
            assert response.headers["content-type"] == "audio/wav"
            assert response.content == test_content
        finally:
            # 清理测试文件
            if os.path.exists(test_file_path):
                os.remove(test_file_path)

    def test_get_audio_file_not_found(self):
        """测试获取不存在的音频文件"""
        response = self.client.get("/api/v1/audio/non_existent.wav")

        assert response.status_code == status.HTTP_404_NOT_FOUND
        data = response.json()
        assert "Audio file not found" in data["message"]

    def test_get_audio_file_unsupported_format(self):
        """测试获取不支持的音频格式"""
        response = self.client.get("/api/v1/audio/test.mp3")

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        data = response.json()
        assert "Only WAV files are supported" in data["message"]

    def test_get_audio_file_with_special_characters(self):
        """测试文件名包含特殊字符的情况"""
        # 创建包含特殊字符的文件名
        test_filename = "test_audio_with_special_chars.wav"
        test_file_path = os.path.join(self.output_dir, test_filename)

        test_content = b"fake wav file content"
        with open(test_file_path, "wb") as f:
            f.write(test_content)

        try:
            response = self.client.get(f"/api/v1/audio/{test_filename}")

            assert response.status_code == status.HTTP_200_OK
            assert response.content == test_content
        finally:
            if os.path.exists(test_file_path):
                os.remove(test_file_path)

    def test_get_audio_file_empty_filename(self):
        """测试空文件名"""
        response = self.client.get("/api/v1/audio/")

        # 这应该返回404，因为路由不匹配
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_get_audio_file_directory_traversal(self):
        """测试目录遍历攻击防护"""
        # 尝试访问上级目录的文件
        response = self.client.get("/api/v1/audio/../../../etc/passwd")

        # 应该返回404，因为文件不存在于outputs目录中
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_get_audio_file_large_file(self):
        """测试大文件处理"""
        test_filename = "large_test.wav"
        test_file_path = os.path.join(self.output_dir, test_filename)

        # 创建一个较大的测试文件（1MB）
        large_content = b"x" * (1024 * 1024)
        with open(test_file_path, "wb") as f:
            f.write(large_content)

        try:
            response = self.client.get(f"/api/v1/audio/{test_filename}")

            assert response.status_code == status.HTTP_200_OK
            assert len(response.content) == len(large_content)
        finally:
            if os.path.exists(test_file_path):
                os.remove(test_file_path)
