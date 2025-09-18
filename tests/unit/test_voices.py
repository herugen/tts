"""
音色管理端点测试
测试 /voices 端点的功能
"""

import pytest
from fastapi import status
from app.models import oc8r
from app.infra.repositories import UploadRepository, VoiceRepository
import uuid
from datetime import datetime


class TestVoiceEndpoint:
    """音色管理端点测试类"""

    def test_create_voice_success(self, test_client, test_db, sample_upload):
        """测试创建音色成功"""
        # 先创建一个上传记录
        upload_repo = UploadRepository(test_db)
        upload_repo.add(sample_upload)

        voice_data = {
            "name": "Test Voice",
            "description": "Test voice description",
            "uploadId": sample_upload.id,
        }

        response = test_client.post("/api/v1/voices", json=voice_data)

        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert "voice" in data
        assert data["voice"]["name"] == "Test Voice"
        assert data["voice"]["description"] == "Test voice description"
        assert data["voice"]["uploadId"] == sample_upload.id
        assert "id" in data["voice"]
        assert "createdAt" in data["voice"]
        assert "updatedAt" in data["voice"]

    def test_create_voice_duplicate_name(self, test_client, test_db, sample_upload):
        """测试创建重复名称的音色"""
        # 先创建一个上传记录
        upload_repo = UploadRepository(test_db)
        upload_repo.add(sample_upload)

        # 创建第一个音色
        voice_data = {
            "name": "Test Voice",
            "description": "First voice",
            "uploadId": sample_upload.id,
        }
        response1 = test_client.post("/api/v1/voices", json=voice_data)
        assert response1.status_code == status.HTTP_201_CREATED

        # 创建第二个音色（相同名称）
        voice_data2 = {
            "name": "Test Voice",
            "description": "Second voice",
            "uploadId": sample_upload.id,
        }
        response2 = test_client.post("/api/v1/voices", json=voice_data2)
        assert response2.status_code == status.HTTP_400_BAD_REQUEST

    def test_create_voice_invalid_upload_id(self, test_client):
        """测试使用无效的上传ID创建音色"""
        voice_data = {
            "name": "Test Voice",
            "description": "Test voice",
            "uploadId": "invalid-upload-id",
        }

        response = test_client.post("/api/v1/voices", json=voice_data)
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_create_voice_missing_required_fields(self, test_client):
        """测试缺少必填字段"""
        # 缺少name
        voice_data = {"description": "Test voice", "uploadId": "test-upload-id"}
        response = test_client.post("/api/v1/voices", json=voice_data)
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT

        # 缺少uploadId
        voice_data = {"name": "Test Voice", "description": "Test voice"}
        response = test_client.post("/api/v1/voices", json=voice_data)
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT

    def test_list_voices_success(
        self, test_client, test_db, sample_upload, sample_voice
    ):
        """测试列举音色成功"""
        # 先创建上传记录和音色记录
        upload_repo = UploadRepository(test_db)
        voice_repo = VoiceRepository(test_db)
        upload_repo.add(sample_upload)
        voice_repo.add(sample_voice)

        response = test_client.get("/api/v1/voices")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "voices" in data
        assert len(data["voices"]) == 1
        assert data["voices"][0]["name"] == sample_voice.name

    def test_list_voices_pagination(self, test_client, test_db, sample_upload):
        """测试音色列表分页"""
        # 创建多个音色记录
        upload_repo = UploadRepository(test_db)
        voice_repo = VoiceRepository(test_db)
        upload_repo.add(sample_upload)

        for i in range(5):
            voice = oc8r.Voice(
                id=str(uuid.uuid4()),
                name=f"Voice {i}",
                description=f"Description {i}",
                uploadId=sample_upload.id,
                createdAt=datetime.now().isoformat(),
                updatedAt=datetime.now().isoformat(),
            )
            voice_repo.add(voice)

        # 测试分页
        response = test_client.get("/api/v1/voices?limit=2&offset=0")
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert len(data["voices"]) == 2

    def test_get_voice_success(self, test_client, test_db, sample_upload, sample_voice):
        """测试获取单个音色成功"""
        # 先创建记录
        upload_repo = UploadRepository(test_db)
        voice_repo = VoiceRepository(test_db)
        upload_repo.add(sample_upload)
        voice_repo.add(sample_voice)

        response = test_client.get(f"/api/v1/voices/{sample_voice.id}")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "voice" in data
        assert data["voice"]["id"] == sample_voice.id
        assert data["voice"]["name"] == sample_voice.name

    def test_get_voice_not_found(self, test_client):
        """测试获取不存在的音色"""
        response = test_client.get("/api/v1/voices/non-existent-id")
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_delete_voice_success(
        self, test_client, test_db, sample_upload, sample_voice
    ):
        """测试删除音色成功"""
        # 先创建记录
        upload_repo = UploadRepository(test_db)
        voice_repo = VoiceRepository(test_db)
        upload_repo.add(sample_upload)
        voice_repo.add(sample_voice)

        response = test_client.delete(f"/api/v1/voices/{sample_voice.id}")

        assert response.status_code == status.HTTP_204_NO_CONTENT
        # 删除成功，无响应体

        # 验证音色已被删除
        get_response = test_client.get(f"/api/v1/voices/{sample_voice.id}")
        assert get_response.status_code == status.HTTP_404_NOT_FOUND

    def test_delete_voice_not_found(self, test_client):
        """测试删除不存在的音色"""
        response = test_client.delete("/api/v1/voices/non-existent-id")
        assert response.status_code == status.HTTP_404_NOT_FOUND
