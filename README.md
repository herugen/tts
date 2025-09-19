# TTS Orchestrator API

## 项目概述

TTS Orchestrator API 是一个基于 IndexTTS HTTP Service 的异步文生语音编排服务，提供完整的音色管理和语音合成能力。本项目采用分层架构设计，支持多种TTS模式，包括音色克隆、情感控制等高级功能。

## 核心功能

### 🎵 音色管理

- **音色克隆**：基于用户上传的音频文件创建个性化音色
- **音色列表**：管理所有已创建的克隆音色
- **音色删除**：删除不需要的音色及其关联文件

### 🎤 语音合成

- **异步TTS任务**：支持文本转语音处理
- **多种控制模式**：
  - `speaker`：使用克隆音色和情感，适用于原声翻译场景。
  - `reference`：基于参考音频控制情感
  - `vector`：使用情感向量精确控制
  - `text`：通过情感描述文本控制
- **任务管理**：支持任务查询、取消、重试等操作

### 📁 文件管理

- **音频上传**：支持 WAV 格式，最大 20MB
- **文件存储**：本地文件系统存储，支持文件访问
- **格式转换**：自动处理不同音频格式

### 🔄 队列管理

- **异步处理**：基于队列的异步任务处理
- **并发控制**：支持任务排队和并发限制
- **状态监控**：实时队列状态和任务进度

## TTS模式详解

### 1. Speaker模式（音色情感克隆）

使用已创建的克隆音色和情感进行语音合成：

```json
{
  "text": "要合成的文本",
  "mode": "speaker",
  "voiceId": "v_123",
  "generationArgs": {
    "doSample": true,
    "topP": 0.8,
    "temperature": 0.8
  }
}
```

### 2. Reference模式（参考音频情感）

基于参考音频控制情感表达：

```json
{
  "text": "要合成的文本",
  "mode": "reference",
  "voiceId": "v_123",
  "emotionAudioId": "upload_456",
  "emotionWeight": 0.8
}
```

### 3. Vector模式（情感向量）

使用情感因子精确控制：

```json
{
  "text": "要合成的文本",
  "mode": "vector",
  "voiceId": "v_123",
  "emotionFactors": {
    "happy": 0.8,
    "angry": 0.1,
    "sad": 0.0,
    "afraid": 0.0,
    "disgusted": 0.0,
    "melancholic": 0.1,
    "surprised": 0.0,
    "calm": 0.0
  },
  "emotionRandom": false
}
```

### 4. Text模式（情感文本）

通过情感描述文本控制：

```json
{
  "text": "要合成的文本",
  "mode": "text",
  "voiceId": "v_123",
  "emotionText": "开心、兴奋的语气"
}
```

## 任务状态说明

- **queued**: 任务已入队，等待处理
- **running**: 任务正在执行中
- **succeeded**: 任务执行成功
- **failed**: 任务执行失败
- **cancelled**: 任务已取消

## 错误处理

### 常见错误码

- **400**: 参数错误
- **401**: 未认证
- **403**: 权限不足
- **404**: 资源未找到
- **413**: 负载过大
- **429**: 服务繁忙/限流
- **500**: 服务内部错误

### 错误响应格式

```json
{
  "code": "ERROR_CODE",
  "message": "错误描述信息"
}
```

## 快速开始

### 1. 环境要求

- Python 3.8+
- SQLite 3
- IndexTTS HTTP Service

### 2. 安装依赖

```bash
pip install -r requirements.txt
```

### 3. 配置环境变量

```bash
export INDEX_TTS_BASE_URL="http://10.0.10.42:8000"
export INDEX_TTS_TIMEOUT="1800.0"
export UPLOAD_DIR="data/uploads"
```

### 4. 启动服务

```bash
make run
```

## 使用示例

### 完整工作流程

#### 1. 上传音频文件

```bash
curl -X POST "http://localhost:8000/api/v1/uploads" \
  -H "Authorization: Bearer <your_token>" \
  -F "file=@voice_sample.wav"
```

#### 2. 创建音色

```bash
curl -X POST "http://localhost:8000/api/v1/voices" \
  -H "Authorization: Bearer <your_token>" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "我的音色",
    "description": "个人专属音色",
    "uploadId": "upload_123"
  }'
```

#### 3. 创建TTS任务

```bash
curl -X POST "http://localhost:8000/api/v1/tts/jobs" \
  -H "Authorization: Bearer <your_token>" \
  -H "Content-Type: application/json" \
  -d '{
    "text": "欢迎使用我们的TTS服务",
    "mode": "speaker",
    "voiceId": "v_123"
  }'
```

#### 4. 查询任务状态

```bash
curl -X GET "http://localhost:8000/api/v1/tts/jobs/job_123" \
  -H "Authorization: Bearer <your_token>"
```

#### 5. 获取生成的音频

```bash
curl -X GET "http://localhost:8000/api/v1/audio/generated_audio.wav"
```

## 测试

项目包含完整的测试套件，支持单元测试和集成测试。

### 运行测试

#### 单元测试
```bash
# 运行所有单元测试
make test

# 或直接运行
python tests/scripts/run_tests.py
```

#### 集成测试
```bash
# 运行端到端集成测试
make integration-test

# 或直接运行
./tests/scripts/run_integration_test.sh
```

#### 运行所有测试
```bash
# 先运行单元测试
make test

# 再运行集成测试  
make integration-test
```

### 测试说明

- **单元测试**: 测试各个组件的独立功能
- **集成测试**: 测试完整的API工作流程，包括：
  - 文件上传和音色创建
  - TTS任务创建和执行
  - 音频文件生成和下载
  - 错误处理和边界情况

### 测试环境

集成测试会自动：
- 启动IndexTTS Mock服务（端口8001）
- 启动TTS主服务（端口8000）
- 运行完整的API测试流程
- 自动清理所有服务进程

详细说明请参考 [tests/scripts/README.md](tests/scripts/README.md)。

## 监控和运维

### 健康检查

```bash
curl -X GET "http://localhost:8000/api/v1/health"
```

### 队列状态监控

```bash
curl -X GET "http://localhost:8000/api/v1/queue/status"
```

## 许可证

本项目采用 MIT 许可证。详情请参阅 [LICENSE](LICENSE) 文件。

## 联系我们

如有问题或建议，请通过以下方式联系：

- 项目Issues: [GitHub Issues](https://github.com/your-repo/issues)
- 邮箱: your-email@example.com

---

**TTS Orchestrator API** - 让语音合成更简单、更智能！
