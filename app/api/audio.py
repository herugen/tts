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

import os
from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse

router = APIRouter()

@router.get(
    "/audio/{filename}",
    summary="获取音频文件",
    tags=["Audio"]
)
async def get_audio_file(filename: str):
    """
    获取音频文件
    - 支持WAV格式音频文件
    - 返回音频文件流
    """
    # 验证文件扩展名
    if not filename.endswith('.wav'):
        raise HTTPException(
            status_code=400, 
            detail="Only WAV files are supported"
        )
    
    # 构建文件路径
    file_path = os.path.join("data/outputs", filename)
    
    # 检查文件是否存在
    if not os.path.exists(file_path):
        raise HTTPException(
            status_code=404, 
            detail="Audio file not found"
        )
    
    # 返回音频文件
    return FileResponse(
        path=file_path,
        media_type="audio/wav",
        filename=filename
    )
