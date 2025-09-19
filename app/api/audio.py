"""
文件级注释：
本模块负责音频文件服务接口，支持访问生成的音频文件。
属于接口层（Interface Layer），处理音频文件的HTTP请求和响应。

接口说明：
- 路由: GET /audio/{filename}
- 功能: 提供音频文件的直接访问
- 支持: WAV格式音频文件流式返回

依赖说明：
- 支持音频文件的流式传输
"""

from fastapi import APIRouter, HTTPException, Depends
from app.dependencies import get_audio_service
from app.application.audio_service import AudioService

router = APIRouter()


@router.get("/audio/{filename}", summary="获取音频文件", tags=["Audio"])
async def get_audio_file(
    filename: str, audio_service: AudioService = Depends(get_audio_service)
):
    """
    获取音频文件
    - 委托给Audio应用服务处理业务逻辑
    """
    # 验证文件名格式
    if not filename:
        raise HTTPException(status_code=400, detail="Filename is required")

    # 检查文件扩展名
    if not filename.endswith(".wav"):
        # 对于不支持的格式，抛出HTTP异常
        raise HTTPException(status_code=400, detail="Only WAV files are supported")
    # 委托给Audio应用服务获取音频文件
    file_response = await audio_service.get_audio_file(filename)
    if not file_response:
        raise HTTPException(status_code=404, detail="Audio file not found")

    return file_response
