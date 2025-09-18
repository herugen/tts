"""
测试数据生成器
用于生成测试用的数据
"""

import uuid
from datetime import datetime
from app.models import oc8r

class TestDataGenerator:
    """测试数据生成器类"""
    
    @staticmethod
    def create_upload(
        filename: str = "test.wav",
        content_type: str = "audio/wav",
        size_bytes: int = 1024,
        duration_seconds: float = 1.5
    ) -> oc8r.Upload:
        """创建测试上传记录"""
        return oc8r.Upload(
            id=str(uuid.uuid4()),
            fileName=filename,
            contentType=content_type,
            sizeBytes=size_bytes,
            durationSeconds=duration_seconds,
            createdAt=datetime.now().isoformat()
        )
    
    @staticmethod
    def create_voice(
        name: str = "Test Voice",
        description: str = "Test voice description",
        upload_id: str = None
    ) -> oc8r.Voice:
        """创建测试音色记录"""
        if upload_id is None:
            upload_id = str(uuid.uuid4())
        
        return oc8r.Voice(
            id=str(uuid.uuid4()),
            name=name,
            description=description,
            uploadId=upload_id,
            createdAt=datetime.now().isoformat(),
            updatedAt=datetime.now().isoformat()
        )
    
    @staticmethod
    def create_tts_job(
        text: str = "Hello world",
        mode: oc8r.TtsMode = oc8r.TtsMode.speaker,
        voice_id: str = None,
        status: oc8r.JobStatus = oc8r.JobStatus.queued
    ) -> oc8r.TtsJob:
        """创建测试TTS任务"""
        if voice_id is None:
            voice_id = str(uuid.uuid4())
        
        return oc8r.TtsJob(
            id=str(uuid.uuid4()),
            type=oc8r.Type.tts,
            status=status,
            createdAt=datetime.now().isoformat(),
            updatedAt=datetime.now().isoformat(),
            request=oc8r.CreateTtsJobRequest(
                text=text,
                mode=mode,
                voiceId=voice_id
            ),
            result=None,
            error=None
        )
    
    @staticmethod
    def create_speaker_mode_request(
        text: str = "Hello world",
        voice_id: str = None
    ) -> oc8r.CreateTtsJobRequest:
        """创建speaker模式请求"""
        if voice_id is None:
            voice_id = str(uuid.uuid4())
        
        return oc8r.CreateTtsJobRequest(
            text=text,
            mode=oc8r.TtsMode.speaker,
            voiceId=voice_id
        )
    
    @staticmethod
    def create_reference_mode_request(
        text: str = "Hello world",
        voice_id: str = None,
        emotion_audio_id: str = None,
        emotion_weight: float = 0.8
    ) -> oc8r.CreateTtsJobRequest:
        """创建reference模式请求"""
        if voice_id is None:
            voice_id = str(uuid.uuid4())
        if emotion_audio_id is None:
            emotion_audio_id = str(uuid.uuid4())
        
        return oc8r.CreateTtsJobRequest(
            text=text,
            mode=oc8r.TtsMode.reference,
            voiceId=voice_id,
            emotionAudioId=emotion_audio_id,
            emotionWeight=emotion_weight
        )
    
    @staticmethod
    def create_vector_mode_request(
        text: str = "Hello world",
        voice_id: str = None,
        emotion_factors: oc8r.EmotionFactors = None
    ) -> oc8r.CreateTtsJobRequest:
        """创建vector模式请求"""
        if voice_id is None:
            voice_id = str(uuid.uuid4())
        if emotion_factors is None:
            emotion_factors = oc8r.EmotionFactors(
                happy=0.8,
                angry=0.1,
                sad=0.0,
                afraid=0.0,
                disgusted=0.0,
                melancholic=0.0,
                surprised=0.1,
                calm=0.0
            )
        
        return oc8r.CreateTtsJobRequest(
            text=text,
            mode=oc8r.TtsMode.vector,
            voiceId=voice_id,
            emotionFactors=emotion_factors
        )
    
    @staticmethod
    def create_text_mode_request(
        text: str = "Hello world",
        voice_id: str = None,
        emotion_text: str = "happy and excited"
    ) -> oc8r.CreateTtsJobRequest:
        """创建text模式请求"""
        if voice_id is None:
            voice_id = str(uuid.uuid4())
        
        return oc8r.CreateTtsJobRequest(
            text=text,
            mode=oc8r.TtsMode.text,
            voiceId=voice_id,
            emotionText=emotion_text
        )
    
    @staticmethod
    def create_generation_args(
        do_sample: bool = True,
        top_p: float = 0.8,
        top_k: int = 30,
        temperature: float = 0.8
    ) -> oc8r.GenerationArgs:
        """创建生成参数"""
        return oc8r.GenerationArgs(
            doSample=do_sample,
            topP=top_p,
            topK=top_k,
            temperature=temperature
        )
    
    @staticmethod
    def create_emotion_factors(
        happy: float = 0.8,
        angry: float = 0.1,
        sad: float = 0.0,
        afraid: float = 0.0,
        disgusted: float = 0.0,
        melancholic: float = 0.0,
        surprised: float = 0.1,
        calm: float = 0.0
    ) -> oc8r.EmotionFactors:
        """创建情感因子"""
        return oc8r.EmotionFactors(
            happy=happy,
            angry=angry,
            sad=sad,
            afraid=afraid,
            disgusted=disgusted,
            melancholic=melancholic,
            surprised=surprised,
            calm=calm
        )
