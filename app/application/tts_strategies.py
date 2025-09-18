"""
TTS策略模式实现

将TTS策略从领域层移动到应用层，作为应用服务的一部分。
策略模式负责不同TTS模式的参数验证和请求构建，属于应用层的技术实现细节。

架构说明：
- TtsStrategy抽象基类定义策略接口
- 四个具体策略类：SpeakerStrategy、ReferenceStrategy、VectorStrategy、TextStrategy
- 每个策略负责对应模式的参数验证和IndexTTS请求构建
- 策略类与IndexTtsClient解耦，便于测试和扩展

依赖说明：
- 依赖app.models.oc8r中的请求模型
- 依赖app.infra.indextts_client.IndexTtsClient
- 依赖app.infra.repositories中的仓储
- 依赖app.infra.storage中的存储服务
"""

from abc import ABC, abstractmethod
from typing import Dict, Any
from app.models import oc8r
from app.infra.indextts_client import IndexTtsClient
from app.infra.repositories import VoiceRepository, UploadRepository
from app.infra.storage import LocalFileStorage
from app.application.file_service import FileApplicationService
import logging

logger = logging.getLogger(__name__)

class TtsStrategy(ABC):
    """
    TTS策略抽象基类
    定义所有TTS策略的通用接口
    """
    
    def __init__(self, client: IndexTtsClient, voice_repo: VoiceRepository, upload_repo: UploadRepository, storage: LocalFileStorage, file_service: FileApplicationService):
        """
        初始化策略
        :param client: IndexTTS客户端实例
        :param voice_repo: Voice仓库实例
        :param upload_repo: Upload仓库实例
        :param storage: 文件存储实例
        :param file_service: 文件处理服务实例
        """
        self.client = client
        self.voice_repo = voice_repo
        self.upload_repo = upload_repo
        self.storage = storage
        self.file_service = file_service
    
    @abstractmethod
    async def validate_request(self, request: oc8r.CreateTtsJobRequest) -> None:
        """
        验证请求参数
        :param request: TTS任务请求
        :raises ValueError: 参数验证失败
        """
        raise NotImplementedError
    
    @abstractmethod
    async def synthesize(self, request: oc8r.CreateTtsJobRequest) -> Dict[str, Any]:
        """
        执行TTS合成
        :param request: TTS任务请求
        :return: 合成结果
        """
        raise NotImplementedError
    
    async def _get_voice_audio_data(self, voice_id: str) -> bytes:
        """
        根据voice_id获取音频文件数据
        :param voice_id: 音色ID
        :return: 音频文件字节数据
        """
        # 获取Voice记录
        voice = self.voice_repo.get(voice_id)
        if not voice:
            raise ValueError(f"Voice {voice_id} not found")
        
        # 获取关联的Upload记录
        upload = self.upload_repo.get(voice.uploadId)
        if not upload:
            raise ValueError(f"Upload record for voice {voice_id} not found")
        
        # 获取音频文件路径
        file_path = self.storage.get_file_path(upload.id)
        if not file_path:
            raise ValueError(f"Audio file for voice {voice_id} not found")
        
        # 读取音频文件
        try:
            with open(file_path, 'rb') as f:
                return f.read()
        except Exception as e:
            raise ValueError(f"Failed to read audio file for voice {voice_id}: {str(e)}") from e
    
    async def _get_emotion_audio_data(self, emotion_audio_id: str) -> bytes:
        """
        根据emotion_audio_id获取情感音频文件数据
        :param emotion_audio_id: 情感音频ID
        :return: 音频文件字节数据
        """
        # 获取Upload记录
        upload = self.upload_repo.get(emotion_audio_id)
        if not upload:
            raise ValueError(f"Emotion audio {emotion_audio_id} not found")
        
        # 获取音频文件路径
        file_path = self.storage.get_file_path(upload.id)
        if not file_path:
            raise ValueError(f"Emotion audio file {emotion_audio_id} not found")
        
        # 读取音频文件
        try:
            with open(file_path, 'rb') as f:
                return f.read()
        except Exception as e:
            raise ValueError(f"Failed to read emotion audio file {emotion_audio_id}: {str(e)}") from e

class SpeakerStrategy(TtsStrategy):
    """
    音色克隆策略
    使用已克隆的音色进行TTS合成
    """
    
    async def validate_request(self, request: oc8r.CreateTtsJobRequest) -> None:
        """
        验证speaker模式请求参数
        """
        if not request.voiceId:
            raise ValueError("voiceId is required for speaker mode")
        
        # speaker模式不需要其他额外参数
        if request.emotionAudioId:
            raise ValueError("emotionAudioId should not be provided for speaker mode")
        if request.emotionFactors:
            raise ValueError("emotionFactors should not be provided for speaker mode")
        if request.emotionText:
            raise ValueError("emotionText should not be provided for speaker mode")
    
    async def synthesize(self, request: oc8r.CreateTtsJobRequest) -> Dict[str, Any]:
        """
        使用音色克隆模式进行TTS合成
        """
        # 获取音色音频数据
        prompt_audio = await self._get_voice_audio_data(request.voiceId)
        
        generation_args = request.generationArgs or oc8r.GenerationArgs()
        # 调用IndexTTS客户端，获取音频数据字节
        audio_data = await self.client.synthesize_speaker(
            text=request.text,
            prompt_audio=prompt_audio,
            generation_args=generation_args
        )
        
        # 使用文件处理服务保存音频文件
        result = await self.file_service.save_audio_result(audio_data)
        return result

class ReferenceStrategy(TtsStrategy):
    """
    参考音频情感策略
    使用参考音频的情感进行TTS合成
    """
    
    async def validate_request(self, request: oc8r.CreateTtsJobRequest) -> None:
        """
        验证reference模式请求参数
        """
        if not request.voiceId:
            raise ValueError("voiceId is required for reference mode")
        if not request.emotionAudioId:
            raise ValueError("emotionAudioId is required for reference mode")
        
        # reference模式不需要其他情感参数
        if request.emotionFactors:
            raise ValueError("emotionFactors should not be provided for reference mode")
        if request.emotionText:
            raise ValueError("emotionText should not be provided for reference mode")
    
    async def synthesize(self, request: oc8r.CreateTtsJobRequest) -> Dict[str, Any]:
        """
        使用参考音频情感模式进行TTS合成
        """
        # 获取音色音频数据
        prompt_audio = await self._get_voice_audio_data(request.voiceId)
        # 获取情感音频数据
        emotion_audio = await self._get_emotion_audio_data(request.emotionAudioId)
        
        generation_args = request.generationArgs or oc8r.GenerationArgs()
        # 调用IndexTTS客户端，获取音频数据字节
        audio_data = await self.client.synthesize_reference(
            text=request.text,
            prompt_audio=prompt_audio,
            emotion_audio=emotion_audio,
            emotion_weight=request.emotionWeight or 0.8,
            generation_args=generation_args
        )
        
        # 使用文件处理服务保存音频文件
        result = await self.file_service.save_audio_result(audio_data)
        return result

class VectorStrategy(TtsStrategy):
    """
    情感向量策略
    使用情感因子向量进行TTS合成
    """
    
    async def validate_request(self, request: oc8r.CreateTtsJobRequest) -> None:
        """
        验证vector模式请求参数
        """
        if not request.voiceId:
            raise ValueError("voiceId is required for vector mode")
        if not request.emotionFactors:
            raise ValueError("emotionFactors is required for vector mode")
        
        # vector模式不需要其他情感参数
        if request.emotionAudioId:
            raise ValueError("emotionAudioId should not be provided for vector mode")
        if request.emotionText:
            raise ValueError("emotionText should not be provided for vector mode")
    
    async def synthesize(self, request: oc8r.CreateTtsJobRequest) -> Dict[str, Any]:
        """
        使用情感向量模式进行TTS合成
        """
        # 获取音色音频数据
        prompt_audio = await self._get_voice_audio_data(request.voiceId)
        
        generation_args = request.generationArgs or oc8r.GenerationArgs()
        # 调用IndexTTS客户端，获取音频数据字节
        audio_data = await self.client.synthesize_vector(
            text=request.text,
            prompt_audio=prompt_audio,
            emotion_factors=request.emotionFactors,
            emotion_random=request.emotionRandom or False,
            generation_args=generation_args
        )
        
        # 使用文件处理服务保存音频文件
        result = await self.file_service.save_audio_result(audio_data)
        return result

class TextStrategy(TtsStrategy):
    """
    情感文本策略
    使用情感描述文本进行TTS合成
    """
    
    async def validate_request(self, request: oc8r.CreateTtsJobRequest) -> None:
        """
        验证text模式请求参数
        """
        if not request.voiceId:
            raise ValueError("voiceId is required for text mode")
        if not request.emotionText:
            raise ValueError("emotionText is required for text mode")
        
        # text模式不需要其他情感参数
        if request.emotionAudioId:
            raise ValueError("emotionAudioId should not be provided for text mode")
        if request.emotionFactors:
            raise ValueError("emotionFactors should not be provided for text mode")
    
    async def synthesize(self, request: oc8r.CreateTtsJobRequest) -> Dict[str, Any]:
        """
        使用情感文本模式进行TTS合成
        """
        # 获取音色音频数据
        prompt_audio = await self._get_voice_audio_data(request.voiceId)
        
        generation_args = request.generationArgs or oc8r.GenerationArgs()
        # 调用IndexTTS客户端，获取音频数据字节
        audio_data = await self.client.synthesize_text(
            text=request.text,
            prompt_audio=prompt_audio,
            emotion_text=request.emotionText,
            emotion_random=request.emotionRandom or False,
            generation_args=generation_args
        )
        
        # 使用文件处理服务保存音频文件
        result = await self.file_service.save_audio_result(audio_data)
        return result

class TtsStrategyFactory:
    """
    TTS策略工厂类
    根据TTS模式创建对应的策略实例
    """
    
    @staticmethod
    def create_strategy(mode: oc8r.TtsMode, client: IndexTtsClient, voice_repo: VoiceRepository, upload_repo: UploadRepository, storage: LocalFileStorage, file_service: FileApplicationService) -> TtsStrategy:
        """
        根据TTS模式创建策略实例
        :param mode: TTS模式
        :param client: IndexTTS客户端
        :param voice_repo: Voice仓库
        :param upload_repo: Upload仓库
        :param storage: 文件存储
        :param file_service: 文件处理服务
        :return: 策略实例
        """
        strategies = {
            oc8r.TtsMode.speaker: SpeakerStrategy,
            oc8r.TtsMode.reference: ReferenceStrategy,
            oc8r.TtsMode.vector: VectorStrategy,
            oc8r.TtsMode.text: TextStrategy
        }
        
        strategy_class = strategies.get(mode)
        if not strategy_class:
            raise ValueError(f"Unsupported TTS mode: {mode}")
        
        return strategy_class(client, voice_repo, upload_repo, storage, file_service)
