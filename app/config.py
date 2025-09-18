"""
文件级注释：
本模块用于集中管理全局配置常量，便于统一维护和修改。遵循分层架构原则，配置项通过依赖注入传递到各层，避免硬编码。

主要配置项说明：
- UPLOAD_DIR: 上传文件的统一存储目录
- MAX_UPLOAD_BYTES: 单个上传文件允许的最大大小（单位：字节）
- ALLOWED_MIME_TYPES: 允许上传的音频 MIME 类型集合
- ALLOWED_EXTENSIONS: 允许上传的音频扩展名集合
"""

import os

# 上传文件存储目录
UPLOAD_DIR = os.getenv("UPLOAD_DIR", "data/uploads")

# 允许上传的音频 MIME 类型集合
ALLOWED_MIME_TYPES = {"audio/wav", "audio/mpeg", "audio/mp4"}

# 允许上传的音频扩展名集合
ALLOWED_EXTENSIONS = {"wav", "mp3", "mp4"}

# 单个上传文件最大允许大小（字节）
MAX_UPLOAD_BYTES = 20 * 1024 * 1024


# IndexTTS服务端点，默认为10.0.10.42:8000
INDEX_TTS_BASE_URL = os.getenv("INDEX_TTS_BASE_URL", "http://10.0.10.42:8000")
# 超时时间，默认30分钟
INDEX_TTS_TIMEOUT = float(os.getenv("INDEX_TTS_TIMEOUT", "1800.0"))
