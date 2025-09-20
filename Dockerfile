# TTS项目Dockerfile
# 基于Python 3.12官方镜像，使用Alpine Linux以减小镜像大小
FROM python:3.12-alpine

# 设置工作目录
WORKDIR /app

# 设置环境变量
ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

# 安装系统依赖
# 安装必要的系统包，包括编译工具和音频处理库
RUN apk add --no-cache \
    gcc \
    musl-dev \
    libffi-dev \
    openssl-dev \
    sqlite \
    && rm -rf /var/cache/apk/*

# 复制依赖文件
COPY requirements-minimal.txt .

# 安装Python依赖
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements-minimal.txt

# 复制应用代码
COPY . .

# 创建必要的目录
RUN mkdir -p data/uploads data/outputs

# 设置目录权限
RUN chmod -R 755 data/

# 暴露端口（FastAPI默认端口9020）
EXPOSE 9020

# 健康检查
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:9020/api/v1/health')" || exit 1

# 启动命令
# 使用uvicorn启动FastAPI应用，绑定到所有接口，启用热重载（开发环境）
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "9020", "--reload"]
