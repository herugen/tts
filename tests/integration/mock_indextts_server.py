#!/usr/bin/env python3
"""
IndexTTS Mock Server
模拟IndexTTS服务的HTTP API，用于真实集成测试

这个服务模拟IndexTTS的四个主要端点：
- /synthesize/speaker: 音色克隆模式
- /synthesize/reference: 参考音频情感模式
- /synthesize/vector: 情感向量模式
- /synthesize/text: 情感文本模式

所有端点都返回Base64编码的WAV音频数据
"""

import asyncio
import base64
import logging
from datetime import datetime
from typing import Optional


import uvicorn
from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 创建FastAPI应用
app = FastAPI(
    title="IndexTTS Mock Server",
    description="模拟IndexTTS服务的HTTP API，用于集成测试",
    version="1.0.0",
)

# 添加CORS中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# 请求模型
class GenerationArgs(BaseModel):
    """生成参数模型"""

    temperature: float = Field(default=0.7, ge=0.0, le=2.0)
    top_p: float = Field(default=0.9, ge=0.0, le=1.0)
    top_k: int = Field(default=50, ge=1, le=100)
    repetition_penalty: float = Field(default=1.0, ge=0.1, le=2.0)
    max_length: int = Field(default=1000, ge=1, le=2000)


class EmotionFactors(BaseModel):
    """情感因子模型"""

    valence: float = Field(default=0.5, ge=-1.0, le=1.0)  # 效价
    arousal: float = Field(default=0.5, ge=-1.0, le=1.0)  # 唤醒度
    dominance: float = Field(default=0.5, ge=-1.0, le=1.0)  # 支配性


class SpeakerRequest(BaseModel):
    """音色克隆请求模型"""

    text: str = Field(..., min_length=1, max_length=1000)
    prompt_audio: str = Field(..., description="Base64编码的音频数据")
    max_text_tokens_per_segment: int = Field(default=120, ge=1, le=500)
    generation_args: Optional[GenerationArgs] = None


class ReferenceRequest(BaseModel):
    """参考音频情感请求模型"""

    text: str = Field(..., min_length=1, max_length=1000)
    prompt_audio: str = Field(..., description="Base64编码的音色参考音频")
    max_text_tokens_per_segment: int = Field(default=120, ge=1, le=500)
    emotion_audio: str = Field(..., description="Base64编码的情感参考音频")
    emotion_weight: float = Field(default=0.8, ge=0.0, le=1.0)
    generation_args: Optional[GenerationArgs] = None


class VectorRequest(BaseModel):
    """情感向量请求模型"""

    text: str = Field(..., min_length=1, max_length=1000)
    prompt_audio: str = Field(..., description="Base64编码的音色参考音频")
    max_text_tokens_per_segment: int = Field(default=120, ge=1, le=500)
    emotion_factors: EmotionFactors
    emotion_random: bool = Field(default=False)
    generation_args: Optional[GenerationArgs] = None


class TextRequest(BaseModel):
    """情感文本请求模型"""

    text: str = Field(..., min_length=1, max_length=1000)
    prompt_audio: str = Field(..., description="Base64编码的音色参考音频")
    max_text_tokens_per_segment: int = Field(default=120, ge=1, le=500)
    emotion_text: str = Field(..., min_length=1, max_length=200)
    emotion_random: bool = Field(default=False)
    generation_args: Optional[GenerationArgs] = None


# 全局状态
processing_requests = 0
max_concurrent_requests = 2  # 模拟服务限制


def create_mock_wav_audio(duration_seconds: float = 2.0) -> bytes:
    """
    创建模拟的WAV音频数据
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


async def simulate_processing_delay():
    """模拟TTS处理的延迟"""
    # 随机延迟1-3秒，模拟真实TTS处理时间
    import random

    delay = random.uniform(1.0, 3.0)
    await asyncio.sleep(delay)


@app.get("/health")
async def health_check():
    """健康检查端点"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "processing_requests": processing_requests,
        "max_concurrent_requests": max_concurrent_requests,
    }


@app.post("/synthesize/speaker")
async def synthesize_speaker(request: SpeakerRequest):
    """
    音色克隆模式TTS合成
    模拟IndexTTS的speaker端点
    """
    global processing_requests

    # 检查并发限制
    if processing_requests >= max_concurrent_requests:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Service is busy, please try again later",
        )

    try:
        processing_requests += 1
        logger.info(f"Processing speaker synthesis request: {request.text[:50]}...")

        # 验证音频数据
        try:
            audio_data = base64.b64decode(request.prompt_audio)
            if len(audio_data) < 100:  # 最小音频长度检查
                raise ValueError("Audio data too short")
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid audio data: {str(e)}",
            )

        # 模拟处理延迟
        await simulate_processing_delay()

        # 生成模拟音频
        duration = min(len(request.text) * 0.1, 10.0)  # 根据文本长度估算时长
        mock_audio = create_mock_wav_audio(duration)

        # 返回Base64编码的音频数据
        audio_base64 = base64.b64encode(mock_audio).decode("utf-8")

        logger.info(f"Speaker synthesis completed, audio size: {len(mock_audio)} bytes")
        return audio_base64

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Speaker synthesis failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Synthesis failed: {str(e)}",
        )
    finally:
        processing_requests -= 1


@app.post("/synthesize/reference")
async def synthesize_reference(request: ReferenceRequest):
    """
    参考音频情感模式TTS合成
    模拟IndexTTS的reference端点
    """
    global processing_requests

    if processing_requests >= max_concurrent_requests:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Service is busy, please try again later",
        )

    try:
        processing_requests += 1
        logger.info(f"Processing reference synthesis request: {request.text[:50]}...")

        # 验证音频数据
        try:
            prompt_audio = base64.b64decode(request.prompt_audio)
            emotion_audio = base64.b64decode(request.emotion_audio)
            if len(prompt_audio) < 100 or len(emotion_audio) < 100:
                raise ValueError("Audio data too short")
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid audio data: {str(e)}",
            )

        # 模拟处理延迟
        await simulate_processing_delay()

        # 生成模拟音频
        duration = min(len(request.text) * 0.1, 10.0)
        mock_audio = create_mock_wav_audio(duration)

        audio_base64 = base64.b64encode(mock_audio).decode("utf-8")

        logger.info(
            f"Reference synthesis completed, audio size: {len(mock_audio)} bytes"
        )
        return audio_base64

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Reference synthesis failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Synthesis failed: {str(e)}",
        )
    finally:
        processing_requests -= 1


@app.post("/synthesize/vector")
async def synthesize_vector(request: VectorRequest):
    """
    情感向量模式TTS合成
    模拟IndexTTS的vector端点
    """
    global processing_requests

    if processing_requests >= max_concurrent_requests:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Service is busy, please try again later",
        )

    try:
        processing_requests += 1
        logger.info(f"Processing vector synthesis request: {request.text[:50]}...")

        # 验证音频数据
        try:
            audio_data = base64.b64decode(request.prompt_audio)
            if len(audio_data) < 100:
                raise ValueError("Audio data too short")
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid audio data: {str(e)}",
            )

        # 模拟处理延迟
        await simulate_processing_delay()

        # 生成模拟音频
        duration = min(len(request.text) * 0.1, 10.0)
        mock_audio = create_mock_wav_audio(duration)

        audio_base64 = base64.b64encode(mock_audio).decode("utf-8")

        logger.info(f"Vector synthesis completed, audio size: {len(mock_audio)} bytes")
        return audio_base64

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Vector synthesis failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Synthesis failed: {str(e)}",
        )
    finally:
        processing_requests -= 1


@app.post("/synthesize/text")
async def synthesize_text(request: TextRequest):
    """
    情感文本模式TTS合成
    模拟IndexTTS的text端点
    """
    global processing_requests

    if processing_requests >= max_concurrent_requests:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Service is busy, please try again later",
        )

    try:
        processing_requests += 1
        logger.info(f"Processing text synthesis request: {request.text[:50]}...")

        # 验证音频数据
        try:
            audio_data = base64.b64decode(request.prompt_audio)
            if len(audio_data) < 100:
                raise ValueError("Audio data too short")
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid audio data: {str(e)}",
            )

        # 模拟处理延迟
        await simulate_processing_delay()

        # 生成模拟音频
        duration = min(len(request.text) * 0.1, 10.0)
        mock_audio = create_mock_wav_audio(duration)

        audio_base64 = base64.b64encode(mock_audio).decode("utf-8")

        logger.info(f"Text synthesis completed, audio size: {len(mock_audio)} bytes")
        return audio_base64

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Text synthesis failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Synthesis failed: {str(e)}",
        )
    finally:
        processing_requests -= 1


if __name__ == "__main__":
    # 启动服务器
    uvicorn.run(
        "mock_indextts_server:app",
        host="0.0.0.0",
        port=8001,  # 使用8001端口，避免与主服务冲突
        reload=True,
        log_level="info",
    )
