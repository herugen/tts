"""
文件级注释：
本模块实现IndexTTS HTTP Service的客户端适配器，负责与底层TTS服务的通信。
遵循适配器模式，封装IndexTTS服务的调用细节，为上层提供统一的接口。

架构说明：
- IndexTtsClient类负责与IndexTTS服务的HTTP通信
- 支持四种TTS模式：speaker、reference、vector、text
- 处理音频文件上传、TTS合成等操作
- 统一错误处理和重试机制

依赖说明：
- 依赖httpx进行HTTP请求
- 依赖app.models.oc8r中的请求/响应模型
- 依赖app.config中的配置项
"""

import httpx
from typing import Optional, Dict, Any
from app.models import oc8r
from app.config import INDEX_TTS_BASE_URL, INDEX_TTS_TIMEOUT
import logging
import base64

logger = logging.getLogger(__name__)


class IndexTtsClient:
    """
    IndexTTS HTTP Service客户端
    负责与底层IndexTTS服务进行通信，提供统一的TTS合成接口
    """

    def __init__(self, base_url: str = None):
        """
        初始化IndexTTS客户端
        :param base_url: IndexTTS服务的基础URL，如果为None则使用配置文件中的默认值
        """
        self.base_url = (base_url or INDEX_TTS_BASE_URL).rstrip("/")
        self.client = httpx.AsyncClient(timeout=INDEX_TTS_TIMEOUT)
        logger.info(
            "IndexTTS client initialized with base_url: %s, timeout: %ds",
            self.base_url,
            INDEX_TTS_TIMEOUT,
        )

    async def close(self):
        """关闭HTTP客户端"""
        await self.client.aclose()

    async def upload_audio(self, file_path: str, filename: str) -> str:
        """
        上传音频文件到IndexTTS服务
        :param file_path: 本地文件路径
        :param filename: 文件名
        :return: 上传后的文件ID
        """
        try:
            with open(file_path, "rb") as f:
                files = {"file": (filename, f, "audio/wav")}
                response = await self.client.post(
                    f"{self.base_url}/upload", files=files
                )
                response.raise_for_status()
                result = response.json()
                return result.get("file_id")
        except Exception as e:
            logger.error("Failed to upload audio file %s: %s", file_path, str(e))
            raise

    async def synthesize_speaker(
        self,
        text: str,
        prompt_audio: bytes,
        generation_args: Optional[oc8r.GenerationArgs] = None,
    ) -> bytes:
        """
        使用音色克隆模式进行TTS合成
        :param text: 要合成的文本
        :param prompt_audio: 音色参考音频的字节数据
        :param generation_args: 生成参数
        :return: 合成结果
        """
        payload = {
            "text": text,
            "prompt_audio": base64.b64encode(prompt_audio).decode("utf-8"),
            "max_text_tokens_per_segment": 120,  # 规范中的默认值
            "generation_args": (generation_args or oc8r.GenerationArgs()).model_dump(),
        }

        return await self._synthesize_speaker(payload)

    async def synthesize_reference(
        self,
        text: str,
        prompt_audio: bytes,
        emotion_audio: bytes,
        emotion_weight: float = 0.8,
        generation_args: Optional[oc8r.GenerationArgs] = None,
    ) -> bytes:
        """
        使用参考音频情感模式进行TTS合成
        :param text: 要合成的文本
        :param prompt_audio: 音色参考音频的字节数据
        :param emotion_audio: 情感参考音频的字节数据
        :param emotion_weight: 情感权重
        :param generation_args: 生成参数
        :return: 合成结果
        """
        payload = {
            "text": text,
            "prompt_audio": base64.b64encode(prompt_audio).decode("utf-8"),
            "max_text_tokens_per_segment": 120,  # 规范中的默认值
            "emotion_audio": base64.b64encode(emotion_audio).decode("utf-8"),
            "emotion_weight": emotion_weight,
            "generation_args": (generation_args or oc8r.GenerationArgs()).model_dump(),
        }

        return await self._synthesize_reference(payload)

    async def synthesize_vector(
        self,
        text: str,
        prompt_audio: bytes,
        emotion_factors: oc8r.EmotionFactors,
        emotion_random: bool = False,
        generation_args: Optional[oc8r.GenerationArgs] = None,
    ) -> bytes:
        """
        使用情感向量模式进行TTS合成
        :param text: 要合成的文本
        :param prompt_audio: 音色参考音频的字节数据
        :param emotion_factors: 情感因子
        :param emotion_random: 是否随机采样
        :param generation_args: 生成参数
        :return: 合成结果
        """
        payload = {
            "text": text,
            "prompt_audio": base64.b64encode(prompt_audio).decode("utf-8"),
            "max_text_tokens_per_segment": 120,  # 规范中的默认值
            "emotion_factors": emotion_factors.model_dump(),
            "emotion_random": emotion_random,
            "generation_args": (generation_args or oc8r.GenerationArgs()).model_dump(),
        }

        return await self._synthesize_vector(payload)

    async def synthesize_text(
        self,
        text: str,
        prompt_audio: bytes,
        emotion_text: str,
        emotion_random: bool = False,
        generation_args: Optional[oc8r.GenerationArgs] = None,
    ) -> bytes:
        """
        使用情感文本模式进行TTS合成
        :param text: 要合成的文本
        :param prompt_audio: 音色参考音频的字节数据
        :param emotion_text: 情感描述文本
        :param emotion_random: 是否随机采样
        :param generation_args: 生成参数
        :return: 合成结果
        """
        payload = {
            "text": text,
            "prompt_audio": base64.b64encode(prompt_audio).decode("utf-8"),
            "max_text_tokens_per_segment": 120,  # 规范中的默认值
            "emotion_text": emotion_text,
            "emotion_random": emotion_random,
            "generation_args": (generation_args or oc8r.GenerationArgs()).model_dump(),
        }

        return await self._synthesize_text(payload)

    async def _synthesize_speaker(self, payload: Dict[str, Any]) -> bytes:
        """
        调用IndexTTS服务的speaker端点进行TTS合成
        """
        return await self._call_synthesize_endpoint("/synthesize/speaker", payload)

    async def _synthesize_reference(self, payload: Dict[str, Any]) -> bytes:
        """
        调用IndexTTS服务的reference端点进行TTS合成
        """
        return await self._call_synthesize_endpoint("/synthesize/reference", payload)

    async def _synthesize_vector(self, payload: Dict[str, Any]) -> bytes:
        """
        调用IndexTTS服务的vector端点进行TTS合成
        """
        return await self._call_synthesize_endpoint("/synthesize/vector", payload)

    async def _synthesize_text(self, payload: Dict[str, Any]) -> bytes:
        """
        调用IndexTTS服务的text端点进行TTS合成
        """
        return await self._call_synthesize_endpoint("/synthesize/text", payload)

    async def _call_synthesize_endpoint(
        self, endpoint: str, payload: Dict[str, Any]
    ) -> bytes:
        """
        调用IndexTTS服务的指定端点进行TTS合成
        :param endpoint: API端点路径
        :param payload: 请求载荷
        :return: 音频数据字节
        """
        try:
            response = await self.client.post(
                f"{self.base_url}{endpoint}", json=payload
            )
            response.raise_for_status()
            result = response.json()

            # IndexTTS规范：直接返回Base64编码的WAV音频字符串
            if isinstance(result, str):
                # 解码Base64字符串，返回音频数据
                audio_data = base64.b64decode(result)
                return audio_data
            else:
                raise ValueError(
                    f"Expected Base64 string response, got: {type(result)}"
                )

        except httpx.HTTPStatusError as e:
            logger.error(
                "IndexTTS HTTP error: %d - %s", e.response.status_code, e.response.text
            )
            raise RuntimeError(
                f"IndexTTS service error: {e.response.status_code}"
            ) from e
        except Exception as e:
            logger.error("IndexTTS synthesis failed: %s", str(e))
            raise

    async def _download_audio(self, audio_url: str) -> bytes:
        """
        下载音频文件
        :param audio_url: 音频文件URL
        :return: 音频文件数据
        """
        try:
            response = await self.client.get(audio_url)
            response.raise_for_status()
            return response.content
        except Exception as e:
            logger.error("Failed to download audio from %s: %s", audio_url, str(e))
            raise
