"""
集成测试
测试完整的业务流程
"""

import pytest
from fastapi import status
from app.models import oc8r
import uuid
from datetime import datetime
from unittest.mock import patch, AsyncMock


class TestIntegration:
    """集成测试类"""

    def test_complete_voice_workflow(self, test_client, test_db):
        """测试完整的音色管理工作流程"""
        # 1. 上传音频文件
        with patch("app.infra.storage.LocalFileStorage.save_upload") as mock_save:
            mock_save.return_value = (
                str(uuid.uuid4()),
                "/tmp/test.wav",
                "audio/wav",
                1024,
            )

            response = test_client.post(
                "/api/v1/uploads",
                files={"file": ("test.wav", b"fake audio data", "audio/wav")},
            )
            assert response.status_code == status.HTTP_201_CREATED
            upload_data = response.json()["upload"]
            upload_id = upload_data["id"]

        # 2. 创建音色
        voice_data = {
            "name": "Test Voice",
            "description": "Test voice description",
            "uploadId": upload_id,
        }
        response = test_client.post("/api/v1/voices", json=voice_data)
        assert response.status_code == status.HTTP_201_CREATED
        voice_data = response.json()["voice"]
        voice_id = voice_data["id"]

        # 3. 查询音色
        response = test_client.get(f"/api/v1/voices/{voice_id}")
        assert response.status_code == status.HTTP_200_OK
        assert response.json()["voice"]["name"] == "Test Voice"

        # 4. 列举音色
        response = test_client.get("/api/v1/voices")
        assert response.status_code == status.HTTP_200_OK
        assert len(response.json()["voices"]) == 1

        # 5. 删除音色
        response = test_client.delete(f"/api/v1/voices/{voice_id}")
        assert response.status_code == status.HTTP_204_NO_CONTENT

        # 6. 验证音色已删除
        response = test_client.get(f"/api/v1/voices/{voice_id}")
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_complete_tts_job_workflow(self, test_client, test_db):
        """测试完整的TTS任务工作流程"""
        # 1. 创建音色（简化版，不实际上传文件）
        voice_id = str(uuid.uuid4())
        upload_id = str(uuid.uuid4())

        # 直接创建数据库记录
        from app.infra.repositories import UploadRepository, VoiceRepository

        upload_repo = UploadRepository(test_db)
        voice_repo = VoiceRepository(test_db)

        upload = oc8r.Upload(
            id=upload_id,
            fileName="test.wav",
            contentType="audio/wav",
            sizeBytes=1024,
            durationSeconds=1.5,
            createdAt=datetime.now().isoformat(),
        )
        upload_repo.add(upload)

        voice = oc8r.Voice(
            id=voice_id,
            name="Test Voice",
            description="Test voice",
            uploadId=upload_id,
            createdAt=datetime.now().isoformat(),
            updatedAt=datetime.now().isoformat(),
        )
        voice_repo.add(voice)

        # 2. 创建TTS任务
        job_data = {"text": "Hello world", "mode": "speaker", "voiceId": voice_id}
        response = test_client.post("/api/v1/tts/jobs", json=job_data)
        assert response.status_code == status.HTTP_202_ACCEPTED
        job_data = response.json()["job"]
        job_id = job_data["id"]

        # 3. 查询任务状态
        response = test_client.get(f"/api/v1/tts/jobs/{job_id}")
        assert response.status_code == status.HTTP_200_OK
        assert response.json()["job"]["status"] == "queued"

        # 4. 列举任务
        response = test_client.get("/api/v1/tts/jobs")
        assert response.status_code == status.HTTP_200_OK
        assert len(response.json()["jobs"]) == 1

        # 5. 取消任务
        response = test_client.post(f"/api/v1/tts/jobs/{job_id}/cancel")
        assert response.status_code == status.HTTP_200_OK
        assert response.json()["job"]["status"] == "cancelled"

    def test_error_handling_workflow(self, test_client):
        """测试错误处理工作流程"""
        # 1. 测试无效的API端点
        response = test_client.get("/api/v1/invalid-endpoint")
        assert response.status_code == status.HTTP_404_NOT_FOUND

        # 2. 测试无效的请求数据
        response = test_client.post("/api/v1/voices", json={})
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT

        # 3. 测试不存在的资源
        response = test_client.get("/api/v1/voices/non-existent-id")
        assert response.status_code == status.HTTP_404_NOT_FOUND

        response = test_client.get("/api/v1/tts/jobs/non-existent-id")
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_queue_status_integration(self, test_client):
        """测试队列状态集成"""
        # 1. 获取初始队列状态
        response = test_client.get("/api/v1/queue/status")
        assert response.status_code == status.HTTP_200_OK
        initial_status = response.json()["status"]
        assert initial_status["maxConcurrency"] == 1

        # 2. 创建一些任务后再次检查状态
        # 这里可以添加更多任务创建逻辑来测试队列状态变化

    def test_health_check_integration(self, test_client):
        """测试健康检查集成"""
        response = test_client.get("/api/v1/health")
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["code"] == 200
        assert data["message"] == "OK"

    @patch("app.infra.indextts_client.IndexTtsClient")
    def test_tts_strategy_integration(self, mock_client_class, test_client, test_db):
        """测试TTS策略集成"""
        # 模拟IndexTTS客户端
        mock_client = AsyncMock()
        mock_client.synthesize_speaker.return_value = {
            "audioUrl": "http://example.com/audio.wav",
            "durationSeconds": 2.5,
            "format": "wav",
        }
        mock_client_class.return_value = mock_client

        # 创建音色
        voice_id = str(uuid.uuid4())
        upload_id = str(uuid.uuid4())

        from app.infra.repositories import UploadRepository, VoiceRepository

        upload_repo = UploadRepository(test_db)
        voice_repo = VoiceRepository(test_db)

        upload = oc8r.Upload(
            id=upload_id,
            fileName="test.wav",
            contentType="audio/wav",
            sizeBytes=1024,
            durationSeconds=1.5,
            createdAt=datetime.now().isoformat(),
        )
        upload_repo.add(upload)

        voice = oc8r.Voice(
            id=voice_id,
            name="Test Voice",
            description="Test voice",
            uploadId=upload_id,
            createdAt=datetime.now().isoformat(),
            updatedAt=datetime.now().isoformat(),
        )
        voice_repo.add(voice)

        # 创建TTS任务
        job_data = {"text": "Hello world", "mode": "speaker", "voiceId": voice_id}
        response = test_client.post("/api/v1/tts/jobs", json=job_data)
        assert response.status_code == status.HTTP_202_ACCEPTED

        # 验证任务已创建
        job_id = response.json()["job"]["id"]
        response = test_client.get(f"/api/v1/tts/jobs/{job_id}")
        assert response.status_code == status.HTTP_200_OK
        assert response.json()["job"]["status"] == "queued"
