#!/bin/bash

# 集成测试脚本
# 负责启动服务、运行测试、清理环境

set -e  # 遇到错误立即退出

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 日志函数
log_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

log_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

log_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

log_error() {
    echo -e "${RED}❌ $1${NC}"
}

# 清理函数
cleanup() {
    log_info "清理服务..."
    
    # 停止Mock服务
    if [ ! -z "$MOCK_PID" ]; then
        kill $MOCK_PID 2>/dev/null || true
    fi
    
    # 停止TTS服务
    if [ ! -z "$TTS_PID" ]; then
        kill $TTS_PID 2>/dev/null || true
    fi
    
    # 强制清理所有相关进程
    pkill -f "tests/integration/mock_indextts_server.py" 2>/dev/null || true
    pkill -f "uvicorn.*main:app" 2>/dev/null || true
    
    log_success "服务清理完成"
}

# 设置退出时清理
trap cleanup EXIT

# 检查依赖
check_dependencies() {
    log_info "检查依赖..."
    
    if ! command -v python3 &> /dev/null; then
        log_error "Python3 未安装"
        exit 1
    fi
    
    if ! command -v curl &> /dev/null; then
        log_error "curl 未安装"
        exit 1
    fi
    
    log_success "依赖检查通过"
}

# 启动Mock服务
start_mock_service() {
    log_info "启动IndexTTS Mock服务..."
    python3 tests/integration/mock_indextts_server.py &
    MOCK_PID=$!
    
    # 等待服务启动
    sleep 5
    log_info "等待Mock服务启动完成..."
    
    # 检查服务是否启动成功
    local max_attempts=30
    local attempt=0
    
    while [ $attempt -lt $max_attempts ]; do
        if curl -s http://localhost:8001/health > /dev/null 2>&1; then
            log_success "Mock服务启动成功"
            return 0
        fi
        sleep 1
        attempt=$((attempt + 1))
    done
    
    log_error "Mock服务启动失败"
    exit 1
}

# 启动TTS服务
start_tts_service() {
    log_info "启动TTS主服务..."
    
    # 设置环境变量
    export INDEX_TTS_BASE_URL=http://localhost:8001
    export TTS_BASE_URL=http://localhost:8000
    
    python3 -m uvicorn app.main:app --host 0.0.0.0 --port 8000 &
    TTS_PID=$!
    
    # 等待服务启动
    sleep 5
    
    # 检查服务是否启动成功
    local max_attempts=30
    local attempt=0
    
    while [ $attempt -lt $max_attempts ]; do
        if curl -s http://localhost:8000/api/v1/health > /dev/null 2>&1; then
            log_success "TTS服务启动成功"
            return 0
        fi
        sleep 1
        attempt=$((attempt + 1))
    done
    
    log_error "TTS服务启动失败"
    exit 1
}

# 运行集成测试
run_integration_test() {
    log_info "运行集成测试..."
    python3 -m pytest tests/integration/test_integration.py -v -s
}

# 主函数
main() {
    log_info "🚀 开始集成测试"
    echo "=================================================="
    
    # 检查依赖
    check_dependencies
    
    # 启动服务
    start_mock_service
    start_tts_service
    
    # 运行测试
    run_integration_test
    
    log_success "🎉 集成测试完成"
}

# 运行主函数
main "$@"
