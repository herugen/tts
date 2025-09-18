"""
依赖注入模块

提供FastAPI依赖注入函数，用于在API层中获取应用服务实例。
遵循依赖注入模式，简化API层的服务获取。

架构说明：
- 提供统一的依赖注入接口
- 支持FastAPI Depends装饰器
- 统一管理服务获取逻辑
- 便于测试和扩展

职责：
- 提供应用服务依赖注入函数
- 管理服务实例的获取
- 支持不同API端点的服务需求
"""

from fastapi import Depends
import sqlite3
from app.container import app_container
from app.db_conn import get_db_conn
from app.application.tts_service import TtsApplicationService
from app.application.voice_service import VoiceApplicationService
from app.application.upload_service import UploadApplicationService
from app.application.queue_service import QueueApplicationService
from app.application.audio_service import AudioApplicationService
from app.application.tts_processor import TtsTaskProcessor


def get_tts_service(db: sqlite3.Connection = Depends(get_db_conn)) -> TtsApplicationService:
    """
    获取TTS应用服务实例
    
    Args:
        db: 数据库连接
        
    Returns:
        TtsApplicationService: TTS应用服务实例
    """
    return app_container.get_tts_service(db)


def get_voice_service(db: sqlite3.Connection = Depends(get_db_conn)) -> VoiceApplicationService:
    """
    获取Voice应用服务实例
    
    Args:
        db: 数据库连接
        
    Returns:
        VoiceApplicationService: Voice应用服务实例
    """
    return app_container.get_voice_service(db)


def get_upload_service(db: sqlite3.Connection = Depends(get_db_conn)) -> UploadApplicationService:
    """
    获取Upload应用服务实例
    
    Args:
        db: 数据库连接
        
    Returns:
        UploadApplicationService: Upload应用服务实例
    """
    return app_container.get_upload_service(db)


def get_queue_service(db: sqlite3.Connection = Depends(get_db_conn)) -> QueueApplicationService:
    """
    获取Queue应用服务实例
    
    Args:
        db: 数据库连接
        
    Returns:
        QueueApplicationService: Queue应用服务实例
    """
    return app_container.get_queue_service(db)


def get_audio_service(db: sqlite3.Connection = Depends(get_db_conn)) -> AudioApplicationService:
    """
    获取Audio应用服务实例
    
    Args:
        db: 数据库连接
        
    Returns:
        AudioApplicationService: Audio应用服务实例
    """
    return app_container.get_audio_service(db)

def get_tts_processor(db: sqlite3.Connection = Depends(get_db_conn)) -> TtsTaskProcessor:
    """
    获取TTS任务处理器实例
    
    Args:
        db: 数据库连接
        
    Returns:
        TtsTaskProcessor: TTS任务处理器实例
    """
    return app_container.get_tts_processor(db)