"""
TTS任务端点测试
测试 /tts/jobs 端点的功能
"""

import pytest
from fastapi import status
from app.models import oc8r
from app.infra.repositories import TtsJobRepository, VoiceRepository, UploadRepository
import uuid
from datetime import datetime
from unittest.mock import patch, AsyncMock


class TestTtsJobEndpoint:
    """TTS任务端点测试类"""

    def test_create_tts_job_speaker_mode(self, test_client, test_db, sample_voice):
        """测试创建speaker模式的TTS任务"""
        # 先创建音色记录
        voice_repo = VoiceRepository(test_db)
        voice_repo.add(sample_voice)

        job_data = {
            "text": "Hello world",
            "mode": "speaker",
            "voiceId": sample_voice.id,
        }

        response = test_client.post("/api/v1/tts/jobs", json=job_data)

        assert response.status_code == status.HTTP_202_ACCEPTED
        data = response.json()
        assert "job" in data
        assert data["job"]["type"] == "tts"
        assert data["job"]["status"] == "queued"
        assert data["job"]["request"]["text"] == "Hello world"
        assert data["job"]["request"]["mode"] == "speaker"
        assert data["job"]["request"]["voiceId"] == sample_voice.id

    def test_create_tts_job_reference_mode(
        self, test_client, test_db, sample_voice, sample_upload
    ):
        """测试创建reference模式的TTS任务"""
        # 先创建记录
        voice_repo = VoiceRepository(test_db)
        upload_repo = UploadRepository(test_db)
        voice_repo.add(sample_voice)
        upload_repo.add(sample_upload)

        job_data = {
            "text": "Hello world",
            "mode": "reference",
            "voiceId": sample_voice.id,
            "emotionAudioId": sample_upload.id,
            "emotionWeight": 0.8,
        }

        response = test_client.post("/api/v1/tts/jobs", json=job_data)

        assert response.status_code == status.HTTP_202_ACCEPTED
        data = response.json()
        assert data["job"]["request"]["mode"] == "reference"
        assert data["job"]["request"]["emotionAudioId"] == sample_upload.id
        assert data["job"]["request"]["emotionWeight"] == 0.8

    def test_create_tts_job_vector_mode(self, test_client, test_db, sample_voice):
        """测试创建vector模式的TTS任务"""
        # 先创建音色记录
        voice_repo = VoiceRepository(test_db)
        voice_repo.add(sample_voice)

        job_data = {
            "text": "Hello world",
            "mode": "vector",
            "voiceId": sample_voice.id,
            "emotionFactors": {
                "happy": 0.8,
                "angry": 0.1,
                "sad": 0.0,
                "afraid": 0.0,
                "disgusted": 0.0,
                "melancholic": 0.0,
                "surprised": 0.1,
                "calm": 0.0,
            },
        }

        response = test_client.post("/api/v1/tts/jobs", json=job_data)

        assert response.status_code == status.HTTP_202_ACCEPTED
        data = response.json()
        assert data["job"]["request"]["mode"] == "vector"
        assert "emotionFactors" in data["job"]["request"]

    def test_create_tts_job_text_mode(self, test_client, test_db, sample_voice):
        """测试创建text模式的TTS任务"""
        # 先创建音色记录
        voice_repo = VoiceRepository(test_db)
        voice_repo.add(sample_voice)

        job_data = {
            "text": "Hello world",
            "mode": "text",
            "voiceId": sample_voice.id,
            "emotionText": "happy and excited",
        }

        response = test_client.post("/api/v1/tts/jobs", json=job_data)

        assert response.status_code == status.HTTP_202_ACCEPTED
        data = response.json()
        assert data["job"]["request"]["mode"] == "text"
        assert data["job"]["request"]["emotionText"] == "happy and excited"

    def test_create_tts_job_missing_required_fields(self, test_client):
        """测试缺少必填字段"""
        # 缺少text
        job_data = {"mode": "speaker", "voiceId": "test-voice-id"}
        response = test_client.post("/api/v1/tts/jobs", json=job_data)
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT

        # 缺少mode
        job_data = {"text": "Hello world", "voiceId": "test-voice-id"}
        response = test_client.post("/api/v1/tts/jobs", json=job_data)
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT

        # 缺少voiceId
        job_data = {"text": "Hello world", "mode": "speaker"}
        response = test_client.post("/api/v1/tts/jobs", json=job_data)
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT

    def test_get_tts_job_success(self, test_client, test_db, sample_tts_job):
        """测试获取TTS任务成功"""
        # 先创建任务记录
        job_repo = TtsJobRepository(test_db)
        job_repo.add(sample_tts_job)

        response = test_client.get(f"/api/v1/tts/jobs/{sample_tts_job.id}")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "job" in data
        assert data["job"]["id"] == sample_tts_job.id
        assert data["job"]["status"] == "queued"

    def test_get_tts_job_not_found(self, test_client):
        """测试获取不存在的TTS任务"""
        response = test_client.get("/api/v1/tts/jobs/non-existent-id")
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_list_tts_jobs_success(self, test_client, test_db, sample_tts_job):
        """测试列举TTS任务成功"""
        # 先创建任务记录
        job_repo = TtsJobRepository(test_db)
        job_repo.add(sample_tts_job)

        response = test_client.get("/api/v1/tts/jobs")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "jobs" in data
        assert len(data["jobs"]) == 1
        assert data["jobs"][0]["id"] == sample_tts_job.id

    def test_cancel_tts_job_success(self, test_client, test_db, sample_tts_job):
        """测试取消TTS任务成功"""
        # 先创建任务记录
        job_repo = TtsJobRepository(test_db)
        job_repo.add(sample_tts_job)

        response = test_client.post(f"/api/v1/tts/jobs/{sample_tts_job.id}/cancel")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "job" in data
        assert data["job"]["status"] == "cancelled"

    def test_cancel_tts_job_not_found(self, test_client):
        """测试取消不存在的TTS任务"""
        response = test_client.post("/api/v1/tts/jobs/non-existent-id/cancel")
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_cancel_tts_job_invalid_status(self, test_client, test_db):
        """测试取消已完成的任务"""
        # 创建一个已完成的任务
        completed_job = oc8r.TtsJob(
            id=str(uuid.uuid4()),
            type=oc8r.Type.tts,
            status=oc8r.JobStatus.succeeded,
            createdAt=datetime.now().isoformat(),
            updatedAt=datetime.now().isoformat(),
            request=oc8r.CreateTtsJobRequest(
                text="Hello world", mode=oc8r.TtsMode.speaker, voiceId="test-voice-id"
            ),
            result=oc8r.Result(audioUrl="http://example.com/audio.wav"),
            error=None,
        )

        job_repo = TtsJobRepository(test_db)
        job_repo.add(completed_job)

        response = test_client.post(f"/api/v1/tts/jobs/{completed_job.id}/cancel")
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_retry_tts_job_success(self, test_client, test_db):
        """测试重试TTS任务成功"""
        # 创建一个失败的任务
        failed_job = oc8r.TtsJob(
            id=str(uuid.uuid4()),
            type=oc8r.Type.tts,
            status=oc8r.JobStatus.failed,
            createdAt=datetime.now().isoformat(),
            updatedAt=datetime.now().isoformat(),
            request=oc8r.CreateTtsJobRequest(
                text="Hello world", mode=oc8r.TtsMode.speaker, voiceId="test-voice-id"
            ),
            result=None,
            error=oc8r.ErrorResponse(code="TTS_ERROR", message="Processing failed"),
        )

        job_repo = TtsJobRepository(test_db)
        job_repo.add(failed_job)

        response = test_client.post(f"/api/v1/tts/jobs/{failed_job.id}/retry")

        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert "job" in data
        assert data["job"]["status"] == "queued"
        assert data["job"]["id"] != failed_job.id  # 应该是新的任务ID

    def test_retry_tts_job_not_found(self, test_client):
        """测试重试不存在的TTS任务"""
        response = test_client.post("/api/v1/tts/jobs/non-existent-id/retry")
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_retry_tts_job_invalid_status(self, test_client, test_db, sample_tts_job):
        """测试重试非失败状态的任务"""
        # 先创建任务记录
        job_repo = TtsJobRepository(test_db)
        job_repo.add(sample_tts_job)

        response = test_client.post(f"/api/v1/tts/jobs/{sample_tts_job.id}/retry")
        assert response.status_code == status.HTTP_400_BAD_REQUEST
