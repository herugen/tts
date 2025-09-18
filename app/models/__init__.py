"""
模型模块初始化文件
导出所有模型类供其他模块使用
"""

# 导入 oc8r 模型（主要业务模型）
from .oc8r import (
    CreateTtsJobRequest,
    TtsJob,
    TtsJobResponse,
    TtsJobListResponse,
    Upload,
    UploadResponse,
    Voice,
    VoiceResponse,
    VoiceListResponse,
    QueueStatus,
    QueueStatusResponse,
    HealthResponse,
    JobStatus,
    TtsMode,
    OutputFormat,
    Type,
    Result,
    Pagination,
    PendingResponse,
    UploadAudioRequest,
    CreateVoiceRequest,
    # 重命名冲突的类
    GenerationArgs as Oc8rGenerationArgs,
    EmotionFactors as Oc8rEmotionFactors,
    ErrorResponse as Oc8rErrorResponse,
)

# 导入 indextts2 模型（API 客户端模型）
from .indextts2 import (
    Base,
    Speaker,
    ReferenceAudio,
    Vectors,
    TextPrompt,
    AudioWav,
    # 重命名冲突的类
    GenerationArgs as IndexTtsGenerationArgs,
    EmotionFactors as IndexTtsEmotionFactors,
    ErrorResponse as IndexTtsErrorResponse,
)

# 为了向后兼容，创建别名
GenerationArgs = Oc8rGenerationArgs
EmotionFactors = Oc8rEmotionFactors
ErrorResponse = Oc8rErrorResponse
