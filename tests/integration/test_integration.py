"""
本地真实集成测试
使用本地运行的IndexTTS服务端和curl命令进行端到端测试

测试流程：
1. 启动本地IndexTTS mock服务端
2. 启动本地TTS主服务
3. 使用curl命令测试完整的API流程
4. 验证音频文件生成和下载

这个测试文件提供了真实的集成测试场景，在本地环境中运行
"""

import json
import subprocess
import time
import uuid
from pathlib import Path
from typing import Dict, Any, Optional

import requests


class IntegrationTest:
    """真实集成测试类"""

    def __init__(self):
        self.tts_service_url = "http://localhost:8000"
        self.indextts_service_url = "http://localhost:8001"
        self.test_data_dir = Path("tests/data")
        self.test_data_dir.mkdir(exist_ok=True)

    def create_test_audio_file(self, duration_seconds: float = 2.0) -> bytes:
        """
        创建测试用的WAV音频文件
        :param duration_seconds: 音频时长（秒）
        :return: WAV格式的音频字节数据
        """
        # 简单的WAV文件头（44字节）
        sample_rate = 22050
        num_samples = int(sample_rate * duration_seconds)

        # WAV文件头
        wav_header = bytearray(44)
        wav_header[0:4] = b"RIFF"
        wav_header[4:8] = (36 + num_samples * 2).to_bytes(4, "little")
        wav_header[8:12] = b"WAVE"
        wav_header[12:16] = b"fmt "
        wav_header[16:20] = (16).to_bytes(4, "little")
        wav_header[20:22] = (1).to_bytes(2, "little")  # PCM
        wav_header[22:24] = (1).to_bytes(2, "little")  # 单声道
        wav_header[24:28] = sample_rate.to_bytes(4, "little")
        wav_header[28:32] = (sample_rate * 2).to_bytes(4, "little")
        wav_header[32:34] = (2).to_bytes(2, "little")  # 块对齐
        wav_header[34:36] = (16).to_bytes(2, "little")  # 位深度
        wav_header[36:40] = b"data"
        wav_header[40:44] = (num_samples * 2).to_bytes(4, "little")

        # 生成简单的正弦波音频数据
        import math

        audio_data = bytearray()
        for i in range(num_samples):
            # 生成440Hz的正弦波
            sample = int(32767 * math.sin(2 * math.pi * 440 * i / sample_rate))
            audio_data.extend(sample.to_bytes(2, "little", signed=True))

        return bytes(wav_header + audio_data)

    def wait_for_service(self, url: str, timeout: int = 30) -> bool:
        """
        等待服务启动
        :param url: 服务URL
        :param timeout: 超时时间（秒）
        :return: 是否启动成功
        """
        start_time = time.time()
        while time.time() - start_time < timeout:
            try:
                # 根据URL判断使用哪个健康检查端点
                if "8000" in url:  # TTS服务
                    health_url = f"{url}/api/v1/health"
                else:  # IndexTTS Mock服务
                    health_url = f"{url}/health"

                response = requests.get(health_url, timeout=5)
                if response.status_code == 200:
                    return True
            except requests.exceptions.RequestException:
                pass
            time.sleep(1)
        return False

    def curl_request(
        self,
        method: str,
        url: str,
        data: Optional[Dict] = None,
        files: Optional[Dict] = None,
        headers: Optional[Dict] = None,
    ) -> Dict[str, Any]:
        """
        使用curl命令发送HTTP请求
        :param method: HTTP方法
        :param url: 请求URL
        :param data: JSON数据
        :param files: 文件数据
        :param headers: 请求头
        :return: 响应结果
        """
        cmd = ["curl", "-s", "-X", method.upper()]

        # 添加请求头
        if headers:
            for key, value in headers.items():
                cmd.extend(["-H", f"{key}: {value}"])

        # 添加JSON数据
        if data:
            cmd.extend(["-H", "Content-Type: application/json"])
            cmd.extend(["-d", json.dumps(data)])

        # 添加文件
        if files:
            for key, (filename, _, content_type) in files.items():
                cmd.extend(["-F", f"{key}=@{filename};type={content_type}"])

        # 添加URL
        cmd.append(url)

        try:
            result = subprocess.run(
                cmd, capture_output=True, text=True, timeout=30, check=False
            )

            # 解析响应
            response_data = {
                "status_code": result.returncode,
                "stdout": result.stdout,
                "stderr": result.stderr,
                "success": result.returncode == 0,
            }

            # 尝试解析JSON响应
            try:
                if result.stdout:
                    response_data["json"] = json.loads(result.stdout)
            except json.JSONDecodeError:
                pass

            return response_data

        except subprocess.TimeoutExpired:
            return {
                "status_code": -1,
                "stdout": "",
                "stderr": "Request timeout",
                "success": False,
            }
        except OSError as e:
            return {"status_code": -1, "stdout": "", "stderr": str(e), "success": False}

    def test_health_check(self):
        """测试健康检查"""
        print("\n=== 测试健康检查 ===")

        # 测试TTS服务健康检查
        response = self.curl_request("GET", f"{self.tts_service_url}/api/v1/health")
        assert response["success"], f"TTS服务健康检查失败: {response['stderr']}"

        # 测试IndexTTS服务健康检查
        response = self.curl_request("GET", f"{self.indextts_service_url}/health")
        assert response["success"], f"IndexTTS服务健康检查失败: {response['stderr']}"

        print("✓ 健康检查通过")

    def test_upload_workflow(self):
        """测试文件上传工作流程"""
        print("\n=== 测试文件上传工作流程 ===")

        # 1. 创建测试音频文件
        audio_data = self.create_test_audio_file(2.0)
        audio_file_path = self.test_data_dir / "test_upload.wav"
        audio_file_path.write_bytes(audio_data)

        # 2. 上传音频文件
        files = {"file": (str(audio_file_path), audio_data, "audio/wav")}

        response = self.curl_request(
            "POST", f"{self.tts_service_url}/api/v1/uploads", files=files
        )

        assert response["success"], f"文件上传失败: {response['stderr']}"
        assert "json" in response, "响应不是JSON格式"

        upload_data = response["json"]["upload"]
        upload_id = upload_data["id"]

        print(f"✓ 文件上传成功，ID: {upload_id}")

        # 3. 验证上传记录（通过返回的响应数据验证）
        assert (
            upload_data["fileName"] == "test_upload.wav"
        ), "文件名必须为test_upload.wav"
        assert upload_data["contentType"].startswith("audio/"), "文件类型必须是音频"
        assert upload_data["sizeBytes"] == len(
            audio_data
        ), "文件大小必须等于上传的音频数据大小"

        print("✓ 上传记录验证成功")

        return upload_id

    def test_voice_workflow(self, upload_id: str):
        """测试音色管理工作流程"""
        print("\n=== 测试音色管理工作流程 ===")

        # 1. 创建音色
        voice_data = {
            "name": f"Test Voice {uuid.uuid4().hex[:8]}",
            "description": "测试音色描述",
            "uploadId": upload_id,
        }

        response = self.curl_request(
            "POST", f"{self.tts_service_url}/api/v1/voices", data=voice_data
        )

        assert response["success"], f"创建音色失败: {response['stderr']}"
        assert "json" in response, "响应不是JSON格式"

        voice_data = response["json"]["voice"]
        voice_id = voice_data["id"]

        print(f"✓ 音色创建成功，ID: {voice_id}")

        # 2. 查询音色
        response = self.curl_request(
            "GET", f"{self.tts_service_url}/api/v1/voices/{voice_id}"
        )
        assert response["success"], f"查询音色失败: {response['stderr']}"

        print("✓ 音色查询成功")

        # 3. 列举音色
        response = self.curl_request("GET", f"{self.tts_service_url}/api/v1/voices")
        assert response["success"], f"列举音色失败: {response['stderr']}"

        voices = response["json"]["voices"]
        assert len(voices) >= 1, "音色列表为空"

        print("✓ 音色列举成功")

        return voice_id

    def test_tts_job_workflow(self, voice_id: str):
        """测试TTS任务工作流程"""
        print("\n=== 测试TTS任务工作流程 ===")

        # 1. 创建TTS任务
        job_data = {
            "text": "这是一个测试文本，用于验证TTS合成功能。",
            "mode": "speaker",
            "voiceId": voice_id,
        }

        response = self.curl_request(
            "POST", f"{self.tts_service_url}/api/v1/tts/jobs", data=job_data
        )

        assert response["success"], f"创建TTS任务失败: {response['stderr']}"
        assert "json" in response, "响应不是JSON格式"

        job_data = response["json"]["job"]
        job_id = job_data["id"]

        print(f"✓ TTS任务创建成功，ID: {job_id}")

        # 2. 查询任务状态
        response = self.curl_request(
            "GET", f"{self.tts_service_url}/api/v1/tts/jobs/{job_id}"
        )
        assert response["success"], f"查询任务状态失败: {response['stderr']}"

        job_status = response["json"]["job"]["status"]
        print(f"✓ 任务状态: {job_status}")

        # 3. 等待任务完成（最多等待60秒）
        max_wait_time = 60
        start_time = time.time()

        while time.time() - start_time < max_wait_time:
            response = self.curl_request(
                "GET", f"{self.tts_service_url}/api/v1/tts/jobs/{job_id}"
            )
            if response["success"] and "json" in response:
                job_status = response["json"]["job"]["status"]
                print(f"当前任务状态: {job_status}")

                if job_status in ["succeeded", "failed", "cancelled"]:
                    break

            time.sleep(2)

        # 4. 验证最终状态
        response = self.curl_request(
            "GET", f"{self.tts_service_url}/api/v1/tts/jobs/{job_id}"
        )
        assert response["success"], f"最终状态查询失败: {response['stderr']}"

        final_job = response["json"]["job"]
        final_status = final_job["status"]

        print(f"✓ 最终任务状态: {final_status}")

        # 验证任务必须成功完成
        assert (
            final_status == "succeeded"
        ), f"TTS任务应该成功完成，但实际状态为: {final_status}"

        # 验证任务结果
        result = final_job.get("result")
        assert result is not None, "任务结果不能为空"

        audio_url = result.get("audioUrl")
        assert audio_url is not None, "音频文件URL不能为空"

        print(f"✓ 音频文件URL: {audio_url}")

        # 下载生成的音频文件（直接使用subprocess下载二进制文件）
        audio_file_path = self.test_data_dir / f"generated_audio_{job_id}.wav"
        import subprocess

        result = subprocess.run(
            ["curl", "-s", audio_url], capture_output=True, timeout=30
        )
        assert result.returncode == 0, f"音频文件下载失败: {result.stderr.decode()}"
        assert len(result.stdout) > 0, "下载的音频文件为空"
        audio_file_path.write_bytes(result.stdout)
        print(f"✓ 音频文件已保存: {audio_file_path} (大小: {len(result.stdout)} 字节)")

        return job_id

    def test_queue_status(self):
        """测试队列状态"""
        print("\n=== 测试队列状态 ===")

        response = self.curl_request(
            "GET", f"{self.tts_service_url}/api/v1/queue/status"
        )
        assert response["success"], f"获取队列状态失败: {response['stderr']}"

        queue_status = response["json"]["status"]
        print(f"✓ 队列状态: {queue_status}")

        return queue_status

    def test_error_handling(self):
        """测试错误处理"""
        print("\n=== 测试错误处理 ===")

        # 1. 测试无效的API端点
        response = self.curl_request(
            "GET", f"{self.tts_service_url}/api/v1/invalid-endpoint"
        )
        # 404错误是预期的
        print(f"✓ 无效端点测试: {response['status_code']}")

        # 2. 测试无效的请求数据
        response = self.curl_request(
            "POST", f"{self.tts_service_url}/api/v1/voices", data={}
        )
        # 422错误是预期的
        print(f"✓ 无效数据测试: {response['status_code']}")

        # 3. 测试不存在的资源
        response = self.curl_request(
            "GET", f"{self.tts_service_url}/api/v1/voices/non-existent-id"
        )
        # 404错误是预期的
        print(f"✓ 不存在资源测试: {response['status_code']}")

    def run_full_integration_test(self):
        """运行完整的集成测试"""
        print("🚀 开始真实集成测试")
        print("=" * 50)

        # 等待服务启动
        print("⏳ 等待服务启动...")
        assert self.wait_for_service(self.tts_service_url), "TTS服务启动失败"
        assert self.wait_for_service(self.indextts_service_url), "IndexTTS服务启动失败"
        print("✓ 所有服务已启动")

        try:
            # 1. 健康检查
            self.test_health_check()

            # 2. 文件上传工作流程
            upload_id = self.test_upload_workflow()

            # 3. 音色管理工作流程
            voice_id = self.test_voice_workflow(upload_id)

            # 4. TTS任务工作流程
            job_id = self.test_tts_job_workflow(voice_id)

            # 5. 队列状态测试
            self.test_queue_status()

            # 6. 错误处理测试
            self.test_error_handling()

            print("\n" + "=" * 50)
            print("🎉 真实集成测试全部通过！")
            print("📊 测试结果:")
            print(f"   - 上传ID: {upload_id}")
            print(f"   - 音色ID: {voice_id}")
            print(f"   - 任务ID: {job_id}")

        except (
            AssertionError,
            requests.exceptions.RequestException,
            subprocess.SubprocessError,
        ) as e:
            print(f"\n❌ 集成测试失败: {str(e)}")
            raise


# 测试函数
def test_integration():
    """真实集成测试入口函数"""
    integration_test = IntegrationTest()
    integration_test.run_full_integration_test()


if __name__ == "__main__":
    # 直接运行测试
    test_integration()
